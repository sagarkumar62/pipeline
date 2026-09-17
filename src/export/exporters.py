import json
import csv
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from src.models.tool import ToolRecord
from src.utils.logging import setup_logger

logger = setup_logger("local_exporter")


class LocalDataExporter:
    """
    Exports validated Tool records to CSV, JSON, JSONL, and produces entity_mapping_log.csv.
    """

    def __init__(self, export_dir: str = "data/exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_all(self, records: List[ToolRecord], mapping_logs: List[Dict[str, Any]]):
        """Runs CSV, JSON, JSONL, and mapping log exports."""
        self.export_json(records)
        self.export_jsonl(records)
        self.export_csv(records)
        self.export_mapping_log(mapping_logs)

    def export_json(self, records: List[ToolRecord]):
        path = self.export_dir / "tools.json"
        data = [r.model_dump(mode="json") for r in records]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Exported {len(records)} records to {path}")

    def export_jsonl(self, records: List[ToolRecord]):
        path = self.export_dir / "tools.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(r.model_dump_json(exclude_none=False) + "\n")
        logger.info(f"Exported {len(records)} records to {path}")

    def export_csv(self, records: List[ToolRecord]):
        path = self.export_dir / "tools.csv"
        rows = []
        for r in records:
            rows.append({
                "id": r.id,
                "entity_type": r.entity_type,
                "name": r.name,
                "description": r.description,
                "url": r.url,
                "official_url": r.official_url,
                "github_repo_url": r.github_repo_url,
                "github_stars": r.github_stars,
                "logo_url": r.logo_url,
                "categories": "|".join(r.categories),
                "company_name": r.company_name,
                "company_url": r.company_url,
                "discovery_source_name": r.discovery_source.name,
                "discovery_source_url": r.discovery_source.url,
                "discovery_source_type": r.discovery_source.source_type,
                "discovery_source_trust_level": r.discovery_source.source_trust_level,
                "external_evidence_available": r.external_evidence_available,
                "external_evidence_url": r.external_evidence_url,
                "evidence_sources_count": len(r.evidence_sources),
                "source_name": r.source.name,
                "source_url": r.source.url,
                "source_type": r.source.source_type,
                "source_trust_level": r.source.source_trust_level,
                "verification_status": r.verification_status,
                "website_verified": r.website_verified,
                "github_repository_verified": r.github_repository_verified,
                "logo_verified": r.logo_verified,
                "description_grounded": r.description_grounded,
                "description_source_type": r.description_source_type,
                "description_generation_method": r.description_generation_method,
                "llm_provider_used": r.llm_provider_used,
                "llm_enrichment_status": r.llm_enrichment_status,
                "quality_score": r.quality_score,
                "collected_at": r.created_at.isoformat()
            })

        df = pd.DataFrame(rows)
        df.to_csv(path, index=False, encoding="utf-8")
        logger.info(f"Exported {len(rows)} records to CSV: {path}")

    def export_mapping_log(self, mapping_logs: List[Dict[str, Any]]):
        path = self.export_dir / "entity_mapping_log.csv"
        if not mapping_logs:
            return

        keys = ["raw_name", "canonical_name", "entity_type", "match_method", "confidence", "source"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for log in mapping_logs:
                writer.writerow({
                    "raw_name": log.get("raw_name"),
                    "canonical_name": log.get("canonical_name"),
                    "entity_type": log.get("entity_type", "TOOL"),
                    "match_method": log.get("match_method", "direct"),
                    "confidence": log.get("confidence", 1.0),
                    "source": log.get("source")
                })
        logger.info(f"Exported entity mapping log ({len(mapping_logs)} entries) to {path}")
