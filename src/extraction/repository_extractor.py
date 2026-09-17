from typing import Dict, Any
from src.extraction.base import BaseExtractor
from src.models.repository import RepositoryRecord
from src.models.base import DiscoverySource, EvidenceSource


class RepositoryExtractor(BaseExtractor):
    """
    Extractor for Repository entities from GitHub API and other repository discovery sources.
    Extracts structured fields and populates RepositoryRecord models with factual provenance.
    """

    def extract(self, raw_item: Dict[str, Any], source_name: str = "GitHub API") -> Dict[str, Any]:
        # Handle raw GitHub API item structure
        owner_info = raw_item.get("owner")
        if isinstance(owner_info, dict):
            owner = owner_info.get("login", "")
        else:
            owner = str(owner_info or "").strip()

        name = (raw_item.get("name") or "").strip()
        html_url = raw_item.get("html_url") or raw_item.get("url") or f"https://github.com/{owner}/{name}"

        license_info = raw_item.get("license")
        license_spdx = None
        if isinstance(license_info, dict):
            license_spdx = license_info.get("spdx_id") or license_info.get("name")
        elif isinstance(license_info, str):
            license_spdx = license_info

        query = raw_item.get("_discovery_query") or "GitHub Repositories Search"
        src_name = raw_item.get("_discovery_source") or source_name

        discovery_src = DiscoverySource(
            name=src_name,
            url=f"https://api.github.com/search/repositories?q={query}",
            source_type="API",
            source_trust_level="HIGH"
        )

        evidence_src = EvidenceSource(
            url=html_url,
            source_type="GITHUB_REPOSITORY",
            trust_level="HIGH",
            evidence_type="CODE_REPOSITORY"
        )

        extracted = {
            "name": name,
            "owner": owner,
            "url": html_url,
            "repository_url": html_url,
            "description": raw_item.get("description"),
            "default_branch": raw_item.get("default_branch", "main"),
            "language": raw_item.get("language"),
            "topics": list(raw_item.get("topics") or []),
            "stars": int(raw_item.get("stargazers_count") or raw_item.get("stars") or 0),
            "forks": int(raw_item.get("forks_count") or raw_item.get("forks") or 0),
            "open_issues": int(raw_item.get("open_issues_count") or raw_item.get("open_issues") or 0),
            "watchers": int(raw_item.get("watchers_count") or raw_item.get("watchers") or 0),
            "license": license_spdx,
            "archived": bool(raw_item.get("archived", False)),
            "fork": bool(raw_item.get("fork", False)),
            "homepage": raw_item.get("homepage"),
            "discovery_source": discovery_src,
            "source": discovery_src,
            "evidence_sources": [evidence_src],
            "categories": list(raw_item.get("topics") or ["Developer Tools"])
        }
        return extracted

    def to_record(self, raw_item: Dict[str, Any], source_name: str = "GitHub API") -> RepositoryRecord:
        extracted = self.extract(raw_item, source_name)
        return RepositoryRecord.create_canonical(**extracted)
