from typing import Dict, Any, List, Optional
from src.utils.urls import normalize_url, extract_domain
from src.utils.hashing import generate_tool_id


PRICING_STANDARD_MAP = {
    "free": "Free",
    "freemium": "Freemium",
    "paid": "Paid",
    "open source": "Open Source",
    "opensource": "Open Source",
    "open-source": "Open Source",
    "commercial": "Paid",
    "subscription": "Paid",
}


class ToolNormalizer:
    """
    Normalizes URLs, canonical names, pricing models, and generates canonical Tool IDs.
    """

    @staticmethod
    def normalize_pricing(pricing_raw: Optional[str]) -> Optional[str]:
        if not pricing_raw:
            return None
        clean = pricing_raw.strip().lower()
        return PRICING_STANDARD_MAP.get(clean, pricing_raw.strip())

    @staticmethod
    def normalize_canonical_name(name: str) -> str:
        """Standardizes name for fuzzy matching (lowercase, removes legal suffixes)."""
        if not name:
            return ""
        norm = name.lower().strip()
        # Remove common business suffixes for matching
        for suffix in [" inc.", " inc", " ltd.", " ltd", " llc.", " llc", " corp.", " corp"]:
            if norm.endswith(suffix):
                norm = norm[:-len(suffix)].strip()
        return norm

    def normalize_record(self, cleaned_record: Dict[str, Any]) -> Dict[str, Any]:
        raw_url = cleaned_record.get("url") or ""
        norm_url = normalize_url(raw_url)
        domain = extract_domain(norm_url)
        
        name = cleaned_record.get("name") or ""
        canonical_name = self.normalize_canonical_name(name)
        stable_id = generate_tool_id(domain, name)
        
        pricing = self.normalize_pricing(cleaned_record.get("pricing_model"))
        
        categories = []
        if cleaned_record.get("category"):
            categories.append(cleaned_record["category"])

        # Official URL: normalize if present, but keep None if None
        raw_official = cleaned_record.get("official_url")
        norm_official_url = normalize_url(raw_official) if raw_official else None
        
        norm_evidence_url = normalize_url(cleaned_record.get("external_evidence_url")) if cleaned_record.get("external_evidence_url") else None

        # GitHub repo URL: normalize but keep distinct from official_url
        raw_github_repo = cleaned_record.get("github_repo_url")
        norm_github_repo = normalize_url(raw_github_repo) if raw_github_repo else None

        normalized = {
            "id": stable_id,
            "name": name,
            "raw_name": cleaned_record.get("raw_name") or name,
            "canonical_name": canonical_name,
            "url": norm_url,
            "official_url": norm_official_url,
            "domain": domain,
            "description": cleaned_record.get("description"),
            "categories": categories,
            "pricing_model": pricing,
            "company_name": cleaned_record.get("company_name"),
            "company_url": normalize_url(cleaned_record.get("company_url")) if cleaned_record.get("company_url") else None,
            "discovery_source_name": cleaned_record.get("discovery_source_name") or cleaned_record.get("source_name", "Unknown Source"),
            "discovery_source_url": normalize_url(cleaned_record.get("discovery_source_url") or cleaned_record.get("source_url") or ""),
            "discovery_source_type": cleaned_record.get("discovery_source_type") or cleaned_record.get("source_type", "UNKNOWN"),
            "discovery_source_trust_level": cleaned_record.get("discovery_source_trust_level") or cleaned_record.get("source_trust_level", "UNKNOWN"),
            "external_evidence_available": cleaned_record.get("external_evidence_available", False),
            "external_evidence_url": norm_evidence_url,
            "evidence_sources": list(cleaned_record.get("evidence_sources") or []),
            # GitHub-specific fields
            "github_repo_url": norm_github_repo,
            "github_stars": cleaned_record.get("github_stars"),
            "github_owner": cleaned_record.get("github_owner"),
            "github_topics": cleaned_record.get("github_topics") or [],
            "is_fork": cleaned_record.get("is_fork", False),
            "is_archived": cleaned_record.get("is_archived", False),
            "readme_content": cleaned_record.get("readme_content"),
            "readme_url": cleaned_record.get("readme_url"),
            "readme_available": cleaned_record.get("readme_available", False),
            "discovery_query": cleaned_record.get("discovery_query"),
            # Legacy
            "source_name": cleaned_record.get("source_name", "Unknown Source"),
            "source_url": normalize_url(cleaned_record.get("source_url") or norm_url),
            "source_type": cleaned_record.get("source_type", "UNKNOWN"),
            "source_trust_level": cleaned_record.get("source_trust_level", "UNKNOWN"),
            "discovery_method": cleaned_record.get("discovery_method", "UNKNOWN")
        }
        return normalized

    normalize = normalize_record

