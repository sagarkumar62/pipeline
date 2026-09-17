from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator
from src.utils.urls import normalize_url, extract_domain
from src.utils.hashing import generate_tool_id
from src.models.base import (
    BaseEntity,
    DiscoverySource,
    SourceMetadata,
    EvidenceSource,
    VerificationEvidence,
    VerificationResult,
    QualityMetrics,
)


class ToolRecord(BaseEntity):
    """
    Canonical Pydantic model for a Tool entity in the AI Orbit Ecosystem.
    Inherits core common fields from BaseEntity.
    """
    entity_type: Literal["TOOL"] = "TOOL"
    official_url: Optional[str] = Field(None, description="Verified official canonical website URL of the tool")

    @field_validator("official_url", mode="before", check_fields=False)
    @classmethod
    def validate_official_url(cls, v: Optional[str]) -> Optional[str]:
        return normalize_url(v) if v else None

    company_name: Optional[str] = Field(None, description="Name of developing company/organization")
    company_url: Optional[str] = Field(None, description="Official URL of developing company")
    pricing_model: Optional[str] = Field(None, description="Pricing model (Free, Freemium, Paid, Open Source)")

    # GitHub metadata
    github_stars: Optional[int] = Field(None, description="GitHub stargazer count from API")
    github_repo_url: Optional[str] = Field(None, description="GitHub repository URL (distinct from official_url)")
    github_repository_verified: bool = Field(False, description="Whether GitHub repository evidence is verified")

    @classmethod
    def create_canonical(cls, **kwargs):
        """Creates a standard model with consistent hashing and source metadata."""
        kwargs["canonical_name"] = kwargs.get("name", "").strip().lower()

        # Sync url if missing but official_url is present
        if "url" not in kwargs and "official_url" in kwargs and kwargs["official_url"]:
            kwargs["url"] = kwargs["official_url"]

        # Ensure discovery_source and legacy source exist
        if "discovery_source" not in kwargs:
            if "source" in kwargs and isinstance(kwargs["source"], DiscoverySource):
                kwargs["discovery_source"] = kwargs["source"]
            else:
                kwargs["discovery_source"] = DiscoverySource(
                    name=kwargs.pop("source_name", "Unknown"),
                    url=kwargs.pop("source_url", ""),
                    source_type=kwargs.pop("source_type", "UNKNOWN"),
                    source_trust_level=kwargs.pop("source_trust_level", "UNKNOWN")
                )
        if "source" not in kwargs:
            kwargs["source"] = kwargs["discovery_source"]

        kwargs.pop("source_name", None)
        kwargs.pop("source_url", None)
        kwargs.pop("source_type", None)
        kwargs.pop("source_trust_level", None)

        if kwargs.get("url") and kwargs.get("name"):
            kwargs["id"] = generate_tool_id(kwargs["url"], kwargs["name"])
        return cls(**kwargs)
