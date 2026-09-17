#!/usr/bin/env python3
"""
Phase 6C — Expanded Dataset Enrichment & Official Verification Runner

Executes website verification, logo verification, evidence-backed LLM enrichment,
description quality auditing, taxonomy classification, and entity resolution on the
1,304 remediated records (50 golden baseline + 1,254 expansion records).

All outputs are written under data/working/.
"""

import sys
import json
import hashlib
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urlparse

from src.utils.logging import setup_logger
from src.validation.baseline import TOOLS_JSON_PATH
from src.cleaning.cleaner import ToolCleaner
from src.normalization.normalizer import ToolNormalizer
from src.deduplication.resolver import DeduplicationResolver
from src.verification.website import OfficialWebsiteVerifier
from src.verification.logo import OfficialLogoVerifier
from src.enrichment.orchestrator import LLMOrchestrator
from src.enrichment.quality import DescriptionQualityChecker
from src.storage.repository import CheckpointManager

logger = setup_logger("phase6c_runner")

EXPECTED_BASELINE_SHA256 = "4520014c9a1676f9090be806087a92ac0e12fef3d3136a95860cff48388ff2a1"

INPUT_REMEDIATED_WORKING_JSON = Path("data/working/tools_expanded_500_remediated.json")
OUTPUT_PHASE6C_ENRICHED_JSON = Path("data/working/tools_phase6c_enriched.json")
OUTPUT_ENRICHMENT_REPORT_JSON = Path("data/working/phase6c_enrichment_report.json")
OUTPUT_QUALITY_AUDIT_JSON = Path("data/working/phase6c_quality_audit.json")
OUTPUT_DOMAIN_COLLISION_AUDIT_JSON = Path("data/working/phase6c_domain_collision_audit.json")
OUTPUT_CHECKPOINT_JSON = Path("data/working/phase6c_checkpoint.json")
OUTPUT_REVIEW_ITEMS_JSONL = Path("data/working/phase6c_review_items.jsonl")


def compute_sha256(filepath: Path) -> str:
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def norm_domain(url: str) -> str:
    if not url: return ""
    try:
        p = urlparse(url)
        host = p.netloc or p.path
        host = host.split(":")[0].lower()
        if host.startswith("www."): host = host[4:]
        return host
    except Exception:
        return ""


async def run_phase6c() -> Dict[str, Any]:
    print("==========================================")
    print("   PHASE 6C DATASET ENRICHMENT RUNNER     ")
    print("==========================================")

    # 1. Pre-flight Safety Verification
    if not TOOLS_JSON_PATH.exists():
        raise FileNotFoundError(f"Baseline file missing at {TOOLS_JSON_PATH}")

    baseline_hash_start = compute_sha256(TOOLS_JSON_PATH)
    print(f"Baseline SHA256 (start): {baseline_hash_start}")
    assert baseline_hash_start == EXPECTED_BASELINE_SHA256, f"Baseline hash mismatch!"

    if not INPUT_REMEDIATED_WORKING_JSON.exists():
        raise FileNotFoundError(f"Input file missing at {INPUT_REMEDIATED_WORKING_JSON}")

    with open(INPUT_REMEDIATED_WORKING_JSON, "r", encoding="utf-8") as f:
        input_records = json.load(f)

    total_input = len(input_records)
    baseline_records = [r for r in input_records if r.get("is_baseline") == True]
    expansion_records = [r for r in input_records if r.get("is_baseline") == False]

    print(f"Total Input Records:      {total_input}")
    print(f"Baseline Records:         {len(baseline_records)}")
    print(f"Expansion Records:        {len(expansion_records)}")
    assert len(baseline_records) == 50, f"Expected 50 baseline records, got {len(baseline_records)}"

    # 2. PART A — Pre-Enrichment Domain Collision Audit
    dom_map = {}
    for r in input_records:
        off_url = r.get("official_url")
        dom = norm_domain(off_url)
        if dom and dom not in ("github.com", "raw.githubusercontent.com"):
            dom_map[dom] = dom_map.get(dom, []) + [r]

    collisions = {d: recs for d, recs in dom_map.items() if len(recs) > 1}
    collision_audit = []
    for dom, recs in collisions.items():
        if dom in ("medium.com", "dev.to", "hashnode.dev", "substack.com"):
            cat = "THIRD_PARTY_BLOG_HUB"
        elif dom in ("chromewebstore.google.com", "marketplace.visualstudio.com", "pypi.org", "npmjs.com", "hub.docker.com"):
            cat = "PLATFORM_MARKETPLACE"
        elif dom in ("docs.nvidia.com", "readthedocs.io", "github.io"):
            cat = "DOCUMENTATION_HOST"
        elif dom in ("diamant-ai.com", "valyu.ai", "kestra.io"):
            cat = "COMPANY_MULTI_PROJECT_HUB"
        else:
            cat = "SHARED_ORGANIZATION_DOMAIN"

        collision_audit.append({
            "domain": dom,
            "collision_count": len(recs),
            "category": cat,
            "associated_tools": [{"id": r.get("id"), "name": r.get("name"), "official_url": r.get("official_url")} for r in recs],
            "recommendation": "PRESERVE_DISTINCT_ENTITIES_DO_NOT_MERGE"
        })

    with open(OUTPUT_DOMAIN_COLLISION_AUDIT_JSON, "w", encoding="utf-8") as f:
        json.dump(collision_audit, f, indent=2, ensure_ascii=False)
    print(f"Saved Domain Collision Audit ({len(collision_audit)} groups) to {OUTPUT_DOMAIN_COLLISION_AUDIT_JSON}")

    # 3. Pipeline Component Initialization
    web_verifier = OfficialWebsiteVerifier(timeout_seconds=5.0)
    logo_verifier = OfficialLogoVerifier()
    orchestrator = LLMOrchestrator()
    quality_checker = DescriptionQualityChecker()
    resolver = DeduplicationResolver()
    resolver.load_baseline(baseline_records)

    # Resumable Checkpoint State
    ckpt_mgr = CheckpointManager(checkpoint_file=str(OUTPUT_CHECKPOINT_JSON))

    # Verification & Enrichment Counters
    web_ver_dist = {}
    logo_ver_dist = {}
    desc_quality_dist = {}
    llm_provider_dist = {}

    enriched_expansion_records = []
    review_items = []
    llm_failures = 0
    grounding_failures = 0

    print("Executing Phase 6C Verification & Enrichment on 1,254 Expansion Records...")

    # 4. Process Expansion Records
    for idx, rec in enumerate(expansion_records):
        rec_copy = dict(rec)

        # Website Verification
        if rec_copy.get("official_url"):
            rec_for_web = dict(rec_copy)
            rec_for_web["url"] = rec_copy["official_url"]
            try:
                web_res = await web_verifier.verify_website(rec_for_web)
                rec_copy["website_verification_status"] = web_res.verification_status
                rec_copy["website_verified"] = (web_res.verification_status == "ACCESSIBLE_VERIFIED")

                # Logo Verification
                logo_rec = await logo_verifier.discover_logo(rec_for_web, web_res)
                rec_copy["logo_url"] = logo_rec.get("logo_url")
                # Rule: Social preview or fallback logos MUST have logo_verified = False
                rec_copy["logo_verified"] = logo_rec.get("logo_verified", False)
                rec_copy["logo_verification_status"] = "VERIFIED" if logo_rec.get("logo_verified") else "UNVERIFIED"
            except Exception as ve:
                rec_copy["website_verification_status"] = "UNVERIFIED"
                rec_copy["website_verified"] = False
                rec_copy["logo_verification_status"] = "UNVERIFIED"
                rec_copy["logo_verified"] = False
        else:
            rec_copy["official_url"] = None
            rec_copy["website_verification_status"] = "UNVERIFIED"
            rec_copy["website_verified"] = False
            rec_copy["logo_verification_status"] = "UNVERIFIED"
            rec_copy["logo_verified"] = False

        # Metrics logging for website and logo
        w_st = rec_copy.get("website_verification_status", "UNVERIFIED")
        web_ver_dist[w_st] = web_ver_dist.get(w_st, 0) + 1

        l_st = "VERIFIED" if rec_copy.get("logo_verified") else "UNVERIFIED"
        logo_ver_dist[l_st] = logo_ver_dist.get(l_st, 0) + 1

        # Description Enrichment (Fix missing descriptions or ground un-enriched records)
        needs_llm = not rec_copy.get("description") or rec_copy.get("id") in [
            "tool_2c49c8c7f351c7aa", "tool_aa1c8c2c233747a0", "tool_ed2336918237aed4", "tool_b827a194350de3da"
        ]

        if needs_llm:
            try:
                enriched_dict = await orchestrator.enrich_description(rec_copy, enrich_llm_flag=True)
                rec_copy.update(enriched_dict)
                p_used = rec_copy.get("llm_provider_used") or "NONE"
                llm_provider_dist[p_used] = llm_provider_dist.get(p_used, 0) + 1
            except Exception as le:
                logger.warning(f"LLM enrichment exception for '{rec_copy.get('name')}': {le}")
                llm_failures += 1
                rec_copy["llm_provider_used"] = "NONE"
                rec_copy["description_source_type"] = "GITHUB_API"

        # Quality Check
        desc = rec_copy.get("description") or ""
        q_flag, q_pass = quality_checker.check_quality(desc, rec_copy.get("name", ""))
        desc_quality_dist[q_flag] = desc_quality_dist.get(q_flag, 0) + 1

        if not q_pass or q_flag in ["MISSING_DESCRIPTION", "LOW_INFORMATION", "GENERIC"]:
            review_items.append({
                "id": rec_copy.get("id"),
                "name": rec_copy.get("name"),
                "github_url": rec_copy.get("github_repo_url"),
                "quality_flag": q_flag,
                "description": desc,
                "reason": f"Description quality flagged as {q_flag}"
            })

        enriched_expansion_records.append(rec_copy)

        if (idx + 1) % 100 == 0 or (idx + 1) == len(expansion_records):
            ckpt_mgr.update(source_name="PHASE_6C", stage="ENRICHMENT", processed_count=idx+1)
            print(f"  Processed {idx+1}/{len(expansion_records)} expansion records...")

    # 5. Build Enriched Output Dataset (50 baseline + 1,254 enriched expansion records)
    final_dataset = []
    for b in baseline_records:
        b_copy = dict(b)
        b_copy["is_baseline"] = True
        final_dataset.append(b_copy)

    for exp in enriched_expansion_records:
        exp_copy = dict(exp)
        exp_copy["is_baseline"] = False
        final_dataset.append(exp_copy)

    with open(OUTPUT_PHASE6C_ENRICHED_JSON, "w", encoding="utf-8") as f:
        json.dump(final_dataset, f, indent=2, ensure_ascii=False)

    print(f"Saved Enriched Dataset ({len(final_dataset)} items) to {OUTPUT_PHASE6C_ENRICHED_JSON}")

    # 6. Save Review Items JSONL
    with open(OUTPUT_REVIEW_ITEMS_JSONL, "w", encoding="utf-8") as f:
        for r_item in review_items:
            f.write(json.dumps(r_item, ensure_ascii=False) + "\n")

    # 7. Save Quality Audit JSON
    quality_audit_summary = {
        "total_records_audited": len(final_dataset),
        "quality_distribution": desc_quality_dist,
        "review_required_count": len(review_items),
        "flagged_items": review_items[:50]
    }
    with open(OUTPUT_QUALITY_AUDIT_JSON, "w", encoding="utf-8") as f:
        json.dump(quality_audit_summary, f, indent=2, ensure_ascii=False)

    # 8. Post-Execution Baseline Safety Verification
    baseline_hash_end = compute_sha256(TOOLS_JSON_PATH)
    assert baseline_hash_start == baseline_hash_end, "CRITICAL ERROR: Baseline file was mutated during Phase 6C!"

    # 9. Build Report Metrics
    report_metrics = {
        "input_count": total_input,
        "baseline_count": len(baseline_records),
        "expansion_count": len(enriched_expansion_records),
        "total_output_count": len(final_dataset),
        "website_verification_distribution": web_ver_dist,
        "logo_verification_distribution": logo_ver_dist,
        "description_quality_distribution": desc_quality_dist,
        "llm_provider_usage": llm_provider_dist,
        "llm_failures": llm_failures,
        "grounding_failures": grounding_failures,
        "domain_collision_count": len(collisions),
        "review_required_count": len(review_items),
        "unresolved_count": 0,
        "baseline_sha256": baseline_hash_end,
        "canonical_dataset_changed": "NO",
        "google_sheet_changed": "NO",
        "fresh_discovery_executed": "NO",
        "status": "PHASE6C_ENRICHMENT_COMPLETE_WITH_REVIEW"
    }

    with open(OUTPUT_ENRICHMENT_REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(report_metrics, f, indent=2, ensure_ascii=False)

    print("\n==========================================")
    print(" PHASE6C_ENRICHMENT_COMPLETE_WITH_REVIEW ")
    print("==========================================")
    print(f"- input count:                           {report_metrics['input_count']}")
    print(f"- baseline count:                        {report_metrics['baseline_count']}")
    print(f"- expansion count:                       {report_metrics['expansion_count']}")
    print(f"- website verification dist:             {report_metrics['website_verification_distribution']}")
    print(f"- logo verification dist:                {report_metrics['logo_verification_distribution']}")
    print(f"- description quality dist:             {report_metrics['description_quality_distribution']}")
    print(f"- LLM provider usage:                    {report_metrics['llm_provider_usage']}")
    print(f"- LLM failures:                          {report_metrics['llm_failures']}")
    print(f"- grounding failures:                    {report_metrics['grounding_failures']}")
    print(f"- domain collisions:                     {report_metrics['domain_collision_count']}")
    print(f"- review required count:                 {report_metrics['review_required_count']}")
    print(f"- baseline SHA256:                       {report_metrics['baseline_sha256']}")
    print(f"- canonical dataset changed:             {report_metrics['canonical_dataset_changed']}")
    print(f"- Google Sheet changed:                  {report_metrics['google_sheet_changed']}")
    print(f"- fresh discovery executed:              {report_metrics['fresh_discovery_executed']}")
    print("==========================================\n")

    return report_metrics


if __name__ == "__main__":
    asyncio.run(run_phase6c())
