from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field, field_validator
from src.utils.urls import normalize_url, extract_domain
from src.models.base import (
    BaseEntity,
    DiscoverySource,
    SourceMetadata,
    EvidenceSource,
    VerificationEvidence,
    VerificationResult,
    QualityMetrics,
)


class MCPRecord(BaseEntity):
    """
    Canonical Pydantic model for a Model Context Protocol (MCP) entity in the AI Orbit Ecosystem.
    Distinguished by entity_type='MCP'.
    """
    entity_type: Literal["MCP"] = "MCP"

    # MCP Specific Metadata Fields
    server_name: Optional[str] = Field(None, description="Official MCP server name identifier")
    package_name: Optional[str] = Field(None, description="Published package name (npm, PyPI, Crates, etc.)")
    repository_url: Optional[str] = Field(None, description="Source code repository URL")
    official_url: Optional[str] = Field(None, description="Official project documentation or landing page")
    registry_url: Optional[str] = Field(None, description="Registry URL where MCP server is indexed")
    npm_package: Optional[str] = Field(None, description="NPM package name if available")
    pypi_package: Optional[str] = Field(None, description="PyPI package name if available")
    docker_image: Optional[str] = Field(None, description="Docker image registry reference if available")
    transport: List[str] = Field(default_factory=list, description="Supported transport layers e.g. stdio, sse, custom")
    capabilities: List[str] = Field(default_factory=list, description="MCP capabilities e.g. tools, prompts, resources")
    integrations: List[str] = Field(default_factory=list, description="Third-party service integrations")
    supported_clients: List[str] = Field(default_factory=list, description="Compatible clients e.g. Claude Desktop, Cursor")
    authentication: Optional[str] = Field(None, description="Authentication mechanism e.g. API key, OAuth, None")
    installation_method: Optional[str] = Field(None, description="Command or instruction e.g. npx -y @modelcontextprotocol/server-etc")
    license: Optional[str] = Field(None, description="License key e.g. MIT, Apache-2.0")
    open_source: bool = Field(True, description="Whether the MCP server is open-source")
    maintainer: Optional[str] = Field(None, description="Maintainer organization or developer username")
    language: Optional[str] = Field(None, description="Implementation language e.g. TypeScript, Python")
    deployment_type: Optional[str] = Field(None, description="Deployment target e.g. Local stdio, Remote SSE, Docker")

    @field_validator("repository_url", mode="before")
    @classmethod
    def validate_mcp_repo_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        norm = normalize_url(v)
        if norm.startswith("http://github.com"):
            norm = "https://github.com" + norm[17:]
        return norm.lower() if "github.com" in norm.lower() else norm

    @field_validator("official_url", mode="before")
    @classmethod
    def validate_mcp_official_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        norm = normalize_url(v)
        return norm if norm else None

    @classmethod
    def create_canonical(cls, **kwargs) -> "MCPRecord":
        """
        Creates an MCPRecord with stable deterministic ID: mcp:<key>
        """
        name = (kwargs.get("name") or kwargs.get("server_name") or "").strip()
        maintainer = (kwargs.get("maintainer") or "").strip().lower()
        repo_url = kwargs.get("repository_url") or kwargs.get("url") or ""
        
        if repo_url:
            repo_url = normalize_url(repo_url)
            kwargs["repository_url"] = repo_url
            kwargs["url"] = repo_url

        if not kwargs.get("canonical_name"):
            kwargs["canonical_name"] = name.lower()

        # Deterministic ID key logic
        if repo_url and "github.com/" in repo_url.lower():
            clean = repo_url.lower().replace("https://github.com/", "").replace("http://github.com/", "").rstrip("/")
            kwargs["id"] = f"mcp:{clean}"
        elif kwargs.get("package_name"):
            clean_pkg = kwargs["package_name"].lower().strip("@").replace("/", "-")
            kwargs["id"] = f"mcp:pkg:{clean_pkg}"
        elif maintainer and name:
            clean_m = maintainer.lower()
            clean_n = name.lower().replace(" ", "-")
            kwargs["id"] = f"mcp:{clean_m}/{clean_n}"
        else:
            clean_n = name.lower().replace(" ", "-")
            kwargs["id"] = f"mcp:{clean_n}"

        # Ensure discovery source
        if "discovery_source" not in kwargs:
            if "source" in kwargs and isinstance(kwargs["source"], DiscoverySource):
                kwargs["discovery_source"] = kwargs["source"]
            else:
                kwargs["discovery_source"] = DiscoverySource(
                    name=kwargs.pop("source_name", "Official MCP Discovery"),
                    url=kwargs.get("url", ""),
                    source_type="OFFICIAL_REGISTRY",
                    source_trust_level="HIGH"
                )
        if "source" not in kwargs:
            kwargs["source"] = kwargs["discovery_source"]

        return cls(**kwargs)
