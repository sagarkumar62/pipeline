from typing import Dict, Any
from src.extraction.base import BaseExtractor
from src.models.mcp import MCPRecord
from src.models.base import DiscoverySource, EvidenceSource


class MCPExtractor(BaseExtractor):
    """
    Extractor for MCP entities from GitHub MCP Search and registry discovery sources.
    Extracts structured MCP metadata fields while preserving provenance.
    """

    def extract(self, raw_item: Dict[str, Any], source_name: str = "GitHub MCP Search") -> Dict[str, Any]:
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

        query = raw_item.get("_discovery_query") or "topic:mcp-server"
        src_name = raw_item.get("_discovery_source") or source_name

        topics = list(raw_item.get("topics") or [])
        desc = (raw_item.get("description") or "").lower()
        combined_text = f"{name} {desc} {' '.join(topics)}".lower()

        # Extract transports only when evidence explicitly supports it
        transports = []
        if "stdio" in combined_text:
            transports.append("stdio")
        if "sse" in combined_text or "server-sent" in combined_text:
            transports.append("sse")

        # Extract capabilities only when evidence explicitly supports it
        capabilities = []
        if "tool" in combined_text or "tools" in combined_text:
            capabilities.append("tools")
        if "prompt" in combined_text or "prompts" in combined_text:
            capabilities.append("prompts")
        if "resource" in combined_text or "resources" in combined_text:
            capabilities.append("resources")

        # Extract supported clients only when evidence explicitly supports it
        supported_clients = []
        if "claude" in combined_text:
            supported_clients.append("Claude Desktop")
        if "cursor" in combined_text:
            supported_clients.append("Cursor")
        if "zed" in combined_text:
            supported_clients.append("Zed")

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
            "server_name": name,
            "maintainer": owner,
            "url": html_url,
            "repository_url": html_url,
            "official_url": raw_item.get("homepage"),
            "description": raw_item.get("description"),
            "categories": ["MCP", "Developer Tools"],
            "language": raw_item.get("language"),
            "license": license_spdx,
            "transport": transports,
            "capabilities": capabilities,
            "supported_clients": supported_clients,
            "open_source": not raw_item.get("private", False),
            "discovery_source": discovery_src,
            "source": discovery_src,
            "evidence_sources": [evidence_src]
        }
        return extracted

    def to_record(self, raw_item: Dict[str, Any], source_name: str = "GitHub MCP Search") -> MCPRecord:
        extracted = self.extract(raw_item, source_name)
        return MCPRecord.create_canonical(**extracted)
