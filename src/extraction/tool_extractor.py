from typing import Dict, Any
from src.extraction.base import BaseExtractor


class ToolExtractor(BaseExtractor):
    """
    Standard extractor for Tool entities from discovery sources.
    Extracts core fields while preserving raw metadata.
    """

    def extract(self, raw_item: Dict[str, Any], source_name: str) -> Dict[str, Any]:
        source_url = raw_item.get("source_url") or raw_item.get("url") or ""
        
        extracted = {
            "name": raw_item.get("name", "").strip(),
            "url": raw_item.get("url", "").strip(),
            "description": raw_item.get("description", "").strip() if raw_item.get("description") else None,
            "category": raw_item.get("category"),
            "company_name": raw_item.get("company_name"),
            "company_url": raw_item.get("company_url"),
            "pricing_model": raw_item.get("pricing_model"),
            "official_url": raw_item.get("official_url"),
            "discovery_source_name": raw_item.get("discovery_source_name") or source_name,
            "discovery_source_url": raw_item.get("discovery_source_url") or source_url,
            "discovery_source_type": raw_item.get("discovery_source_type") or raw_item.get("source_type", "UNKNOWN"),
            "discovery_source_trust_level": raw_item.get("discovery_source_trust_level") or raw_item.get("source_trust_level", "UNKNOWN"),
            "external_evidence_available": raw_item.get("external_evidence_available", False),
            "external_evidence_url": raw_item.get("external_evidence_url"),
            "evidence_sources": list(raw_item.get("evidence_sources") or []),
            # GitHub-specific fields
            "github_repo_url": raw_item.get("github_repo_url"),
            "github_stars": raw_item.get("github_stars"),
            "github_owner": raw_item.get("github_owner"),
            "github_topics": raw_item.get("github_topics") or [],
            "is_fork": raw_item.get("is_fork", False),
            "is_archived": raw_item.get("is_archived", False),
            "readme_content": raw_item.get("readme_content"),
            "readme_url": raw_item.get("readme_url"),
            "readme_available": raw_item.get("readme_available", False),
            "discovery_query": raw_item.get("discovery_query"),
            # Legacy fields
            "source_name": source_name,
            "source_url": source_url,
            "source_type": raw_item.get("source_type", "UNKNOWN"),
            "source_trust_level": raw_item.get("source_trust_level", "UNKNOWN"),
            "discovery_method": raw_item.get("discovery_method", "UNKNOWN"),
            "raw_payload": raw_item
        }
        return extracted
