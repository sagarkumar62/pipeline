import json
from pathlib import Path
from typing import Dict, List, Any
from src.models.tool import ToolRecord
from src.utils.logging import setup_logger

logger = setup_logger("relationship_mapper")


class RelationshipMapper:
    """
    Maps ecosystem graph relationships:
    Company --[develops]--> Tool
    """

    def generate_relationships(self, records: List[ToolRecord], output_path: str = "data/validated/relationships.json"):
        relationships = []

        for record in records:
            if record.company_name:
                edge = {
                    "source_entity": record.company_name,
                    "source_type": "COMPANY",
                    "relationship": "develops",
                    "target_id": record.id,
                    "target_name": record.name,
                    "target_type": "TOOL",
                    "evidence": {
                        "official_website": record.url,
                        "company_url": record.company_url
                    }
                }
                relationships.append(edge)

        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(relationships, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported {len(relationships)} relationships to {output_path}")
        return relationships
