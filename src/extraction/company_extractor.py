from typing import Dict, Any
from src.extraction.base import BaseExtractor
from src.models.company import CompanyRecord
from src.models.base import DiscoverySource, EvidenceSource


class CompanyExtractor(BaseExtractor):
    """
    Extractor for Company entities from GitHub Organizations API and discovery sources.
    Extracts structured Company metadata fields while preserving provenance.
    """

    def extract(self, raw_item: Dict[str, Any], source_name: str = "GitHub Organizations API") -> Dict[str, Any]:
        login = str(raw_item.get("login") or "").strip()
        name = str(raw_item.get("name") or raw_item.get("company_name") or login).strip()
        if not name:
            name = login

        html_url = raw_item.get("html_url") or raw_item.get("url") or f"https://github.com/{login}"
        official_url = raw_item.get("blog") or raw_item.get("official_url") or raw_item.get("website")

        if official_url and not official_url.startswith("http"):
            official_url = "https://" + official_url

        query = raw_item.get("_discovery_query") or "type:org ai"
        src_name = raw_item.get("_discovery_source") or source_name

        desc = (raw_item.get("description") or raw_item.get("bio") or "").lower()
        name_lower = name.lower()
        combined_text = f"{name_lower} {desc} {login.lower()}"

        # Classify company type based on explicit evidence
        company_type = "AI Software Company"
        if any(k in combined_text for k in ["infrastructure", "cloud", "compute", "gpu", "chip", "hardware"]):
            company_type = "AI Infrastructure Company"
        elif any(k in combined_text for k in ["research", "lab", "foundation", "openai", "anthropic", "deepmind"]):
            company_type = "AI Research Company"
        elif any(k in combined_text for k in ["robotics", "robot", "autonomous-vehicle"]):
            company_type = "Robotics Company"
        elif any(k in combined_text for k in ["startup", "labs", "incubator"]):
            company_type = "AI Startup"
        elif any(k in combined_text for k in ["enterprise", "b2b", "platform"]):
            company_type = "Enterprise AI Company"

        discovery_src = DiscoverySource(
            name=src_name,
            url=f"https://api.github.com/search/users?q={query}",
            source_type="API",
            source_trust_level="HIGH"
        )

        evidence_src = EvidenceSource(
            url=official_url or html_url,
            source_type="OFFICIAL_WEBSITE" if official_url else "GITHUB_REPOSITORY",
            trust_level="HIGH",
            evidence_type="WEBSITE_META" if official_url else "CODE_REPOSITORY"
        )

        extracted = {
            "name": name,
            "company_name": name,
            "url": official_url or html_url,
            "official_url": official_url,
            "github_url": html_url,
            "description": raw_item.get("description") or raw_item.get("bio"),
            "categories": ["Company", "Artificial Intelligence"],
            "company_type": company_type,
            "status": "ACTIVE",
            "active": True,
            "discovery_source": discovery_src,
            "source": discovery_src,
            "evidence_sources": [evidence_src]
        }
        return extracted

    def to_record(self, raw_item: Dict[str, Any], source_name: str = "GitHub Organizations API") -> CompanyRecord:
        extracted = self.extract(raw_item, source_name)
        return CompanyRecord.create_canonical(**extracted)
