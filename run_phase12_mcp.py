import asyncio
import json
import os
from pathlib import Path
from datetime import datetime, timezone

from src.discovery.mcp_discovery import MCPAdapter
from src.extraction.mcp_extractor import MCPExtractor
from src.qualification.mcp_qualifier import MCPQualifier
from src.deduplication.mcp_resolver import MCPDeduplicationResolver
from src.verification.website import OfficialWebsiteVerifier
from src.models.mcp import MCPRecord
from src.utils.logging import setup_logger

logger = setup_logger("run_phase12_mcp")


async def main():
    logger.info("=== STARTING PHASE 12: MCP MODULE INGESTION RUN ===")

    out_dir = Path("data/working/mcp")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Discovery
    adapter = MCPAdapter(max_pages_per_query=2, per_page=30)
    raw_candidates = []
    target_raw_count = 110

    logger.info(f"Discovering candidate MCP entities (target ~{target_raw_count})...")
    async for raw_item in adapter.discover(limit=target_raw_count):
        raw_candidates.append(raw_item)

    raw_path = out_dir / "mcp_raw.jsonl"
    with open(raw_path, "w", encoding="utf-8") as f:
        for c in raw_candidates:
            f.write(json.dumps(c) + "\n")
    logger.info(f"Saved {len(raw_candidates)} raw candidate items to {raw_path}")

    # 2. Extraction & Qualification
    extractor = MCPExtractor()
    qualifier = MCPQualifier()

    qualified_records = []
    rejected_records = []
    review_records = []

    for item in raw_candidates:
        record = extractor.to_record(item)
        rec_dict = record.model_dump(mode="json")
        status, reason = qualifier.qualify(rec_dict)

        rec_dict["qualification_status"] = status
        rec_dict["qualification_reason"] = reason

        if status == "QUALIFIED":
            qualified_records.append(rec_dict)
        elif status == "HARD_EXCLUSION":
            rejected_records.append(rec_dict)
        else:
            review_records.append(rec_dict)

    # Save qualification stage files
    with open(out_dir / "mcp_qualified.jsonl", "w", encoding="utf-8") as f:
        for r in qualified_records:
            f.write(json.dumps(r) + "\n")

    with open(out_dir / "mcp_rejected.jsonl", "w", encoding="utf-8") as f:
        for r in rejected_records:
            f.write(json.dumps(r) + "\n")

    with open(out_dir / "mcp_review.jsonl", "w", encoding="utf-8") as f:
        for r in review_records:
            f.write(json.dumps(r) + "\n")

    logger.info(f"MCP Qualification Complete: Qualified={len(qualified_records)}, Rejected={len(rejected_records)}, Review={len(review_records)}")

    # 3. Deduplication
    resolver = MCPDeduplicationResolver()
    deduped_records = []
    duplicates_count = 0

    for rec in qualified_records:
        resolved, is_dup = resolver.resolve(rec)
        if is_dup:
            duplicates_count += 1
        else:
            deduped_records.append(resolved)

    logger.info(f"MCP Deduplication Complete: Unique={len(deduped_records)}, Duplicates={duplicates_count}")

    # 4. Website Verification & Logo Semantics
    final_records = []

    for r in deduped_records:
        homepage = r.get("official_url") or r.get("homepage")

        # Rule: github.com repository URLs are NOT external official websites!
        if homepage and "github.com" not in homepage.lower():
            r["website_verified"] = False
            r["verification_status"] = "ACCESSIBLE_UNVERIFIED"
            r["official_url"] = homepage
        else:
            r["website_verified"] = False
            r["verification_status"] = "REPOSITORY_PROVENANCE_ONLY"
            r["official_url"] = None

        # Logo semantics: Do NOT mark github opengraph preview as verified logo
        r["logo_url"] = None
        r["logo_verified"] = False
        r["logo_found"] = False

        # Calculate completeness quality score
        score = 0.6  # Base score for verified MCP provenance & metadata
        if r.get("description"):
            score += 0.2
        if r.get("transport"):
            score += 0.1
        if r.get("website_verified", False):
            score += 0.1

        r["quality_score"] = round(score, 2)
        r["updated_at"] = datetime.now(timezone.utc).isoformat()
        final_records.append(r)

    # 5. Output Final Artifacts
    final_path = out_dir / "mcp_final.json"
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(final_records, f, indent=2)

    manifest = {
        "module": "mcp",
        "phase": "PHASE_12",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "raw_candidates_count": len(raw_candidates),
        "qualified_count": len(qualified_records),
        "rejected_count": len(rejected_records),
        "review_count": len(review_records),
        "duplicates_resolved": duplicates_count,
        "final_records_count": len(final_records),
        "website_verified_count": sum(1 for r in final_records if r.get("website_verified")),
        "output_files": {
            "raw": str(out_dir / "mcp_raw.jsonl"),
            "qualified": str(out_dir / "mcp_qualified.jsonl"),
            "rejected": str(out_dir / "mcp_rejected.jsonl"),
            "review": str(out_dir / "mcp_review.jsonl"),
            "final": str(final_path),
        }
    }

    manifest_path = out_dir / "mcp_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"=== PHASE 12 MCP INGESTION COMPLETE. Final count: {len(final_records)} records saved to {final_path} ===")


if __name__ == "__main__":
    asyncio.run(main())
