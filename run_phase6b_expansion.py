#!/usr/bin/env python3
"""
Phase 6B — Discovery Expansion Toward 500 Qualified Unique Tools Runner

Executes multi-slice GitHub discovery, qualification, deduplication, and provenance tracking
anchored against the 50-record immutable golden baseline.
Outputs working datasets to data/working/ and prints the Phase 6B quality gates report.
"""

import sys
import json
import hashlib
import asyncio
from pathlib import Path
from typing import List, Dict, Any

from src.utils.logging import setup_logger
from src.validation.baseline import BaselineManifestManager, TOOLS_JSON_PATH, MANIFEST_PATH
from src.discovery.tool_discovery import GitHubToolDiscovery
from src.cleaning.cleaner import ToolCleaner
from src.normalization.normalizer import ToolNormalizer
from src.deduplication.resolver import DeduplicationResolver
from src.qualification.qualifier import GitHubRepoQualifier
from src.verification.website import OfficialWebsiteVerifier
from src.verification.logo import OfficialLogoVerifier
from src.storage.repository import CheckpointManager, StorageRepository

logger = setup_logger("phase6b_runner")

EXPECTED_BASELINE_SHA256 = "4520014c9a1676f9090be806087a92ac0e12fef3d3136a95860cff48388ff2a1"
EXPANSION_CANDIDATES_JSONL = Path("data/working/expansion_candidates.jsonl")
EXPANSION_WORKING_JSON = Path("data/working/tools_expanded_500.json")
CHECKPOINT_FILE = Path("data/working/expansion_checkpoint.json")


def compute_sha256(filepath: Path) -> str:
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


async def run_phase6b_expansion(limit: int = 1500) -> Dict[str, Any]:
    print("==========================================")
    print("   PHASE 6B DISCOVERY EXPANSION RUNNER    ")
    print("==========================================")

    # 1. Verification of baseline immutability & pre-flight assertions
    if not TOOLS_JSON_PATH.exists():
        raise FileNotFoundError(f"Baseline file missing at {TOOLS_JSON_PATH}")

    baseline_hash_start = compute_sha256(TOOLS_JSON_PATH)
    print(f"Baseline file:           {TOOLS_JSON_PATH}")
    print(f"Baseline SHA256 (start): {baseline_hash_start}")

    if baseline_hash_start != EXPECTED_BASELINE_SHA256:
        raise ValueError(f"Baseline SHA256 mismatch! Expected {EXPECTED_BASELINE_SHA256}, got {baseline_hash_start}")

    # Load baseline records
    with open(TOOLS_JSON_PATH, "r", encoding="utf-8") as f:
        baseline_records = json.load(f)

    print(f"Baseline record count:   {len(baseline_records)}")
    assert len(baseline_records) == 50, f"Expected 50 baseline records, got {len(baseline_records)}"

    # 2. Initialize Resolver and load baseline as immutable anchors
    resolver = DeduplicationResolver()
    loaded_baseline_count = resolver.load_baseline(baseline_records)
    print(f"Anchored in Resolver:    {loaded_baseline_count} records")

    # 3. Initialize pipeline components
    ckpt_mgr = CheckpointManager(checkpoint_file=str(CHECKPOINT_FILE))
    storage = StorageRepository()
    cleaner = ToolCleaner()
    normalizer = ToolNormalizer()
    qualifier = GitHubRepoQualifier()
    web_verifier = OfficialWebsiteVerifier(timeout_seconds=5.0)
    logo_verifier = OfficialLogoVerifier()

    github_discovery = GitHubToolDiscovery(checkpoint_manager=ckpt_mgr)

    # Metrics counters
    raw_candidates_discovered = 0
    qualified_candidates = 0
    rejected_candidates = 0
    review_candidates = 0
    baseline_duplicates = 0
    intra_expansion_duplicates = 0

    accepted_expansion_records: List[Dict[str, Any]] = []

    # Resume from existing working candidates if present to ensure idempotency
    existing_expansion_ids = set()
    if EXPANSION_CANDIDATES_JSONL.exists():
        with open(EXPANSION_CANDIDATES_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    accepted_expansion_records.append(rec)
                    existing_expansion_ids.add(rec["id"])
                    # Pre-load into resolver so resumed run doesn't duplicate
                    resolver.resolve(rec)
        print(f"Resumed from working state: loaded {len(accepted_expansion_records)} existing unique expansion records")

    # Ensure output dir exists
    EXPANSION_CANDIDATES_JSONL.parent.mkdir(parents=True, exist_ok=True)

    # 4. Execute Discovery & Ingestion
    print(f"Executing GitHub discovery across query slices (limit={limit})...")
    async for raw_candidate in github_discovery.discover(limit=limit):
        raw_candidates_discovered += 1

        # Qualification Gate
        qual_res = qualifier.qualify(raw_candidate)
        status = qual_res.status

        if status == "REJECTED_NON_TOOL":
            rejected_candidates += 1
            storage.save_rejected(raw_candidate, "; ".join(qual_res.reasons), "QUALIFICATION")
            continue
        elif status == "REVIEW_REQUIRED":
            review_candidates += 1
            storage.save_rejected(raw_candidate, "; ".join(qual_res.reasons), "REVIEW_REQUIRED")
            continue

        qualified_candidates += 1

        # Cleaning & Normalization
        cleaned = cleaner.clean(raw_candidate)
        normalized = normalizer.normalize(cleaned)
        norm_dict = normalized if isinstance(normalized, dict) else normalized.model_dump()


        # Entity Resolution (against baseline anchors + previously accepted expansion entities)
        resolved_rec, is_dup = resolver.resolve(norm_dict)

        if is_dup:
            if resolved_rec.get("is_baseline_match"):
                baseline_duplicates += 1
                logger.debug(f"Baseline duplicate skipped: '{resolved_rec['name']}'")
            else:
                intra_expansion_duplicates += 1
                logger.debug(f"Intra-expansion duplicate skipped: '{resolved_rec['name']}'")
            continue

        # Check if already saved in previous run
        if resolved_rec["id"] in existing_expansion_ids:
            continue

        # Lightweight provenance & domain verification (no proxy bypass!)
        if resolved_rec.get("official_url"):
            rec_for_web = dict(resolved_rec)
            rec_for_web["url"] = resolved_rec["official_url"]
            try:
                web_res = await web_verifier.verify_website(rec_for_web)
                resolved_rec["website_verification_status"] = web_res.verification_status
                logo_rec = await logo_verifier.discover_logo(rec_for_web, web_res)
                resolved_rec["logo_url"] = logo_rec.get("logo_url")
                resolved_rec["logo_verified"] = logo_rec.get("logo_verified", False)
                resolved_rec["logo_verification_status"] = "VERIFIED" if logo_rec.get("logo_verified") else "UNVERIFIED"
            except Exception as ve:
                logger.warning(f"Verification error for {resolved_rec['name']}: {ve}")
                resolved_rec["website_verification_status"] = "UNVERIFIED"
                resolved_rec["logo_verification_status"] = "UNVERIFIED"
        else:
            resolved_rec["website_verification_status"] = "UNVERIFIED"
            resolved_rec["logo_verification_status"] = "UNVERIFIED"


        accepted_expansion_records.append(resolved_rec)
        existing_expansion_ids.add(resolved_rec["id"])

        # Stream accepted candidate to JSONL working file
        with open(EXPANSION_CANDIDATES_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(resolved_rec, ensure_ascii=False) + "\n")

    # 5. Build merged working dataset (50 baseline + accepted expansion records)
    total_unique_records = len(baseline_records) + len(accepted_expansion_records)

    all_working_records = []
    # Add baseline records with tag
    for b in baseline_records:
        rec_copy = dict(b)
        rec_copy["is_baseline"] = True
        all_working_records.append(rec_copy)

    # Add unique expansion records
    for exp in accepted_expansion_records:
        rec_copy = dict(exp)
        rec_copy["is_baseline"] = False
        all_working_records.append(rec_copy)

    with open(EXPANSION_WORKING_JSON, "w", encoding="utf-8") as f:
        json.dump(all_working_records, f, indent=2, ensure_ascii=False)

    # 6. Post-execution baseline immutability check
    baseline_hash_end = compute_sha256(TOOLS_JSON_PATH)
    assert baseline_hash_start == baseline_hash_end, "CRITICAL ERROR: Baseline file was mutated during Phase 6B!"

    # 7. Quality Gates Calculation
    total_eval = raw_candidates_discovered if raw_candidates_discovered > 0 else 1
    total_dups = baseline_duplicates + intra_expansion_duplicates
    total_processed = qualified_candidates + total_dups if (qualified_candidates + total_dups) > 0 else 1

    qualification_rate = round((qualified_candidates / total_eval) * 100, 2)
    duplicate_rate = round((total_dups / total_processed) * 100, 2)

    # Provenance metrics
    records_with_legitimate_source = sum(1 for r in accepted_expansion_records if r.get("source_url") or r.get("github_repo_url"))
    records_missing_official_website = sum(1 for r in accepted_expansion_records if not r.get("official_url"))
    records_github_only_provenance = sum(1 for r in accepted_expansion_records if r.get("github_repo_url") and not r.get("official_url"))

    report_metrics = {
        "baseline_records": len(baseline_records),
        "baseline_sha256": baseline_hash_end,
        "raw_candidates_discovered": raw_candidates_discovered,
        "qualified_candidates": qualified_candidates,
        "rejected_candidates": rejected_candidates,
        "review_candidates": review_candidates,
        "baseline_duplicates": baseline_duplicates,
        "intra_expansion_duplicates": intra_expansion_duplicates,
        "unique_expansion_records": len(accepted_expansion_records),
        "total_unique_records_including_baseline": total_unique_records,
        "qualification_rate": qualification_rate,
        "duplicate_rate": duplicate_rate,
        "records_with_legitimate_source_urls": records_with_legitimate_source,
        "records_missing_official_website": records_missing_official_website,
        "records_with_github_only_provenance": records_github_only_provenance,
        "canonical_dataset_changed": "NO",
        "google_sheet_changed": "NO",
        "llm_executed": "NO",
        "proxy_bypass_mechanisms": "NONE"
    }

    # 8. Print Final Report
    print("\n==========================================")
    print(" PHASE6B_DISCOVERY_EXPANSION_COMPLETE     ")
    print("==========================================")
    print(f"- baseline records:                      {report_metrics['baseline_records']}")
    print(f"- baseline SHA256:                       {report_metrics['baseline_sha256']}")
    print(f"- raw candidates discovered:             {report_metrics['raw_candidates_discovered']}")
    print(f"- qualified candidates:                  {report_metrics['qualified_candidates']}")
    print(f"- rejected candidates:                   {report_metrics['rejected_candidates']}")
    print(f"- review candidates:                     {report_metrics['review_candidates']}")
    print(f"- baseline duplicates:                   {report_metrics['baseline_duplicates']}")
    print(f"- intra-expansion duplicates:            {report_metrics['intra_expansion_duplicates']}")
    print(f"- unique expansion records:              {report_metrics['unique_expansion_records']}")
    print(f"- total unique records (with baseline):  {report_metrics['total_unique_records_including_baseline']}")
    print(f"- qualification rate:                    {report_metrics['qualification_rate']}%")
    print(f"- duplicate rate:                        {report_metrics['duplicate_rate']}%")
    print(f"- legitimate source URL coverage:        {report_metrics['records_with_legitimate_source_urls']}")
    print(f"- missing official website count:        {report_metrics['records_missing_official_website']}")
    print(f"- GitHub-only provenance count:          {report_metrics['records_with_github_only_provenance']}")
    print(f"- canonical dataset changed:             {report_metrics['canonical_dataset_changed']}")
    print(f"- Google Sheet changed:                  {report_metrics['google_sheet_changed']}")
    print(f"- LLM executed:                          {report_metrics['llm_executed']}")
    print(f"- proxy/bypass mechanisms:               {report_metrics['proxy_bypass_mechanisms']}")
    print("==========================================\n")

    return report_metrics


if __name__ == "__main__":
    asyncio.run(run_phase6b_expansion())
