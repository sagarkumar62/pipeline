#!/usr/bin/env python3
"""
Phase 6B — Qualification Remediation Runner

Re-evaluates the existing Phase 6B candidate stream using the hardened
GitHubRepoQualifier. Preserves original discovery evidence and outputs
remediated working datasets to data/working/.
"""

import json
import hashlib
import asyncio
from pathlib import Path
from typing import List, Dict, Any

from src.utils.logging import setup_logger
from src.validation.baseline import TOOLS_JSON_PATH
from src.cleaning.cleaner import ToolCleaner
from src.normalization.normalizer import ToolNormalizer
from src.deduplication.resolver import DeduplicationResolver
from src.qualification.qualifier import GitHubRepoQualifier
from src.verification.website import OfficialWebsiteVerifier
from src.verification.logo import OfficialLogoVerifier

logger = setup_logger("phase6b_remediation")

EXPECTED_BASELINE_SHA256 = "4520014c9a1676f9090be806087a92ac0e12fef3d3136a95860cff48388ff2a1"
ORIGINAL_CANDIDATES_JSONL = Path("data/working/expansion_candidates.jsonl")
REMEDIATED_CANDIDATES_JSONL = Path("data/working/expansion_candidates_remediated.jsonl")
REMEDIATED_WORKING_JSON = Path("data/working/tools_expanded_500_remediated.json")
REMEDIATION_SUMMARY_JSON = Path("data/working/expansion_remediation_summary.json")


def compute_sha256(filepath: Path) -> str:
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


async def run_phase6b_remediation() -> Dict[str, Any]:
    print("==========================================")
    print(" PHASE 6B QUALIFICATION REMEDIATION RUN  ")
    print("==========================================")

    # 1. Verify baseline integrity
    if not TOOLS_JSON_PATH.exists():
        raise FileNotFoundError(f"Baseline file missing at {TOOLS_JSON_PATH}")

    baseline_hash_start = compute_sha256(TOOLS_JSON_PATH)
    print(f"Baseline SHA256 (start): {baseline_hash_start}")
    assert baseline_hash_start == EXPECTED_BASELINE_SHA256, f"Baseline hash mismatch!"

    with open(TOOLS_JSON_PATH, "r", encoding="utf-8") as f:
        baseline_records = json.load(f)

    assert len(baseline_records) == 50, f"Expected 50 baseline records, got {len(baseline_records)}"
    print(f"Baseline records:        {len(baseline_records)}")

    # 2. Initialize Resolver and load baseline as immutable anchors
    resolver = DeduplicationResolver()
    resolver.load_baseline(baseline_records)

    cleaner = ToolCleaner()
    normalizer = ToolNormalizer()
    qualifier = GitHubRepoQualifier()

    # 3. Load evidence stream
    orig_candidates = []
    if ORIGINAL_CANDIDATES_JSONL.exists():
        with open(ORIGINAL_CANDIDATES_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    orig_candidates.append(json.loads(line))

    print(f"Original candidate stream: {len(orig_candidates)} items")

    # Metrics
    raw_candidates_count = 1500  # Total raw candidates from Phase 6B
    new_qualified_count = 0
    new_review_count = 0
    new_rejected_count = 0
    baseline_duplicates = 0
    intra_expansion_duplicates = 0

    old_qualified_to_new_rejected = []
    old_qualified_to_new_review = []
    old_qualified_still_qualified = []

    remediated_accepted_records: List[Dict[str, Any]] = []
    existing_remediated_ids = set()

    # Clean remediated output file if present
    if REMEDIATED_CANDIDATES_JSONL.exists():
        REMEDIATED_CANDIDATES_JSONL.unlink()

    # 4. Process all 1314 formerly qualified candidates through hardened qualifier
    print("Re-evaluating candidates through hardened qualifier...")
    for rec in orig_candidates:
        qual_res = qualifier.qualify(rec)
        status = qual_res.status

        old_status = "QUALIFIED_TOOL"
        change_info = {
            "name": rec.get("name"),
            "github_url": rec.get("github_repo_url") or rec.get("url"),
            "old_decision": old_status,
            "new_decision": status,
            "reasons": qual_res.reasons,
        }

        if status == "REJECTED_NON_TOOL":
            new_rejected_count += 1
            old_qualified_to_new_rejected.append(change_info)
            continue
        elif status == "REVIEW_REQUIRED":
            new_review_count += 1
            old_qualified_to_new_review.append(change_info)
            continue

        new_qualified_count += 1
        old_qualified_still_qualified.append(change_info)

        # Cleaning & Normalization
        cleaned = cleaner.clean(rec)
        normalized = normalizer.normalize(cleaned)
        norm_dict = normalized if isinstance(normalized, dict) else normalized.model_dump()

        # Deduplication against baseline + remediated expansion anchors
        resolved_rec, is_dup = resolver.resolve(norm_dict)

        if is_dup:
            if resolved_rec.get("is_baseline_match"):
                baseline_duplicates += 1
            else:
                intra_expansion_duplicates += 1
            continue

        if resolved_rec["id"] in existing_remediated_ids:
            continue

        remediated_accepted_records.append(resolved_rec)
        existing_remediated_ids.add(resolved_rec["id"])

        # Stream to remediated jsonl
        with open(REMEDIATED_CANDIDATES_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(resolved_rec, ensure_ascii=False) + "\n")

    # Add back the originally rejected/review counts from the 1500 discovery run
    new_rejected_count += 26
    new_review_count += 84

    # 5. Build remediated working dataset (50 baseline + remediated unique expansion)
    all_remediated_records = []
    for b in baseline_records:
        r_copy = dict(b)
        r_copy["is_baseline"] = True
        all_remediated_records.append(r_copy)

    for exp in remediated_accepted_records:
        r_copy = dict(exp)
        r_copy["is_baseline"] = False
        all_remediated_records.append(r_copy)

    with open(REMEDIATED_WORKING_JSON, "w", encoding="utf-8") as f:
        json.dump(all_remediated_records, f, indent=2, ensure_ascii=False)

    # 6. Save remediation summary JSON
    summary_data = {
        "raw_candidates_discovered": raw_candidates_count,
        "old_qualified_count": len(orig_candidates),
        "new_qualified_count": new_qualified_count,
        "new_review_count": new_review_count,
        "new_rejected_count": new_rejected_count,
        "baseline_duplicates": baseline_duplicates,
        "intra_expansion_duplicates": intra_expansion_duplicates,
        "new_unique_expansion_count": len(remediated_accepted_records),
        "total_working_dataset_count": len(all_remediated_records),
        "old_qualified_to_new_rejected_count": len(old_qualified_to_new_rejected),
        "old_qualified_to_new_review_count": len(old_qualified_to_new_review),
        "old_qualified_still_qualified_count": len(old_qualified_still_qualified),
        "old_qualified_to_new_rejected": old_qualified_to_new_rejected,
        "old_qualified_to_new_review": old_qualified_to_new_review,
    }

    with open(REMEDIATION_SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

    # 7. Post-run baseline immutability check
    baseline_hash_end = compute_sha256(TOOLS_JSON_PATH)
    assert baseline_hash_start == baseline_hash_end, "Baseline mutated!"

    # 8. Report metrics
    print("\n==========================================")
    print(" PHASE6B_QUALIFICATION_REMEDIATION_COMPLETE ")
    print("==========================================")
    print(f"- raw candidates:                        {raw_candidates_count}")
    print(f"- new qualified count:                  {new_qualified_count}")
    print(f"- new review count:                     {new_review_count}")
    print(f"- new rejected count:                   {new_rejected_count}")
    print(f"- baseline duplicates:                   {baseline_duplicates}")
    print(f"- intra-expansion duplicates:            {intra_expansion_duplicates}")
    print(f"- new unique expansion count:            {len(remediated_accepted_records)}")
    print(f"- total working dataset count:          {len(all_remediated_records)}")
    print(f"- old qualified -> new rejected:         {len(old_qualified_to_new_rejected)}")
    print(f"- old qualified -> new review:           {len(old_qualified_to_new_review)}")
    print(f"- old qualified -> still qualified:      {len(old_qualified_still_qualified)}")
    print(f"- baseline SHA256:                       {baseline_hash_end}")
    print(f"- canonical dataset changed:             NO")
    print(f"- Google Sheet changed:                  NO")
    print(f"- LLM executed:                          NO")
    print(f"- fresh discovery executed:              NO")
    print("==========================================\n")

    return summary_data


if __name__ == "__main__":
    asyncio.run(run_phase6b_remediation())
