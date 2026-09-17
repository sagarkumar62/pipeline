import hashlib
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


class RepositoryRecord(BaseEntity):
    """
    Canonical Pydantic model for a Repository entity in the AI Orbit Ecosystem.
    Distinguished by entity_type='REPOSITORY'.
    """
    entity_type: Literal["REPOSITORY"] = "REPOSITORY"

    # Repository Specific Fields
    owner: str = Field(..., description="GitHub organization or user owner name")
    repository_url: str = Field(..., description="Canonical GitHub repository URL (authoritative provenance)")
    default_branch: Optional[str] = Field("main", description="Primary repository branch")
    language: Optional[str] = Field(None, description="Primary programming language")
    topics: List[str] = Field(default_factory=list, description="Repository topics/tags")
    stars: int = Field(0, description="Stargazer count")
    forks: int = Field(0, description="Fork count")
    open_issues: int = Field(0, description="Open issues count")
    watchers: int = Field(0, description="Subscribers/watchers count")
    license: Optional[str] = Field(None, description="License SPDX key or name")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    pushed_at: Optional[datetime] = Field(None, description="Last git commit push timestamp")
    archived: bool = Field(False, description="Whether the repository is archived")
    fork: bool = Field(False, description="Whether the repository is a fork")
    homepage: Optional[str] = Field(None, description="Project homepage URL provided in repository metadata")
    readme_summary: Optional[str] = Field(None, description="Extracted README summary evidence")

    @field_validator("repository_url", mode="before")
    @classmethod
    def validate_repo_url(cls, v: str) -> str:
        if not v:
            return ""
        norm = normalize_url(v)
        if norm.startswith("http://github.com"):
            norm = "https://github.com" + norm[17:]
        return norm.lower() if "github.com" in norm.lower() else norm

    @field_validator("homepage", mode="before")
    @classmethod
    def validate_homepage_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        norm = normalize_url(v)
        return norm if norm else None

    @classmethod
    def create_canonical(cls, **kwargs) -> "RepositoryRecord":
        """
        Creates a RepositoryRecord with stable deterministic ID: repository:<owner>/<name>
        """
        owner = kwargs.get("owner", "").strip().lower()
        name = kwargs.get("name", "").strip().lower()
        repo_url = kwargs.get("repository_url") or kwargs.get("url") or f"https://github.com/{owner}/{name}"
        if repo_url:
            repo_url = repo_url.lower()
            if repo_url.startswith("http://"):
                repo_url = "https://" + repo_url[7:]
        
        kwargs["repository_url"] = normalize_url(repo_url)
        kwargs["url"] = kwargs["repository_url"]

        if not kwargs.get("canonical_name"):
            kwargs["canonical_name"] = name

        # Deterministic ID format: repository:<owner>/<name>
        if owner and name:
            kwargs["id"] = f"repository:{owner}/{name}"
        elif kwargs.get("url"):
            clean = kwargs["url"].replace("https://", "").replace("http://", "").rstrip("/")
            kwargs["id"] = f"repository:{clean}"

        # Ensure discovery source
        if "discovery_source" not in kwargs:
            if "source" in kwargs and isinstance(kwargs["source"], DiscoverySource):
                kwargs["discovery_source"] = kwargs["source"]
            else:
                kwargs["discovery_source"] = DiscoverySource(
                    name=kwargs.pop("source_name", "GitHub API"),
                    url=kwargs.get("url", ""),
                    source_type="API",
                    source_trust_level="HIGH"
                )
        if "source" not in kwargs:
            kwargs["source"] = kwargs["discovery_source"]

        return cls(**kwargs)
