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


class CompanyRecord(BaseEntity):
    """
    Canonical Pydantic model for a Company entity in the AI Orbit Ecosystem.
    Distinguished by entity_type='COMPANY'.
    
    A Company represents an actual organization/company whose business identity has meaningful AI relevance.
    Products, projects, and directories are distinguished from canonical Company records.
    """
    entity_type: Literal["COMPANY"] = "COMPANY"

    # Company Specific Metadata Fields
    company_name: Optional[str] = Field(None, description="Official company display name e.g. OpenAI")
    legal_name: Optional[str] = Field(None, description="Full legal corporate name e.g. OpenAI, Inc.")
    aliases: List[str] = Field(default_factory=list, description="Known company name aliases or previous names")
    founded_year: Optional[int] = Field(None, description="Year company was founded e.g. 2015")
    headquarters: Optional[str] = Field(None, description="Headquarters city/state e.g. San Francisco, CA")
    country: Optional[str] = Field(None, description="Primary country of operation e.g. USA, UK, France")
    regions: List[str] = Field(default_factory=list, description="Operational regions e.g. North America, Global")
    industry: Optional[str] = Field(None, description="Primary industry sector e.g. Artificial Intelligence, Enterprise Software")
    company_type: Optional[str] = Field(None, description="E.g. AI Startup, AI Research Company, AI Infrastructure Company, AI Software Company, Foundation Model Company")
    ai_focus: Optional[str] = Field(None, description="Core AI domain focus e.g. LLMs, Computer Vision, AI Agents, AI Hardware")
    products: List[str] = Field(default_factory=list, description="Key AI products or platforms developed")
    services: List[str] = Field(default_factory=list, description="Services provided e.g. Custom Model Training, AI API Access")
    technologies: List[str] = Field(default_factory=list, description="Core AI technologies e.g. Transformers, RLHF, MoE, CUDA")
    business_model: Optional[str] = Field(None, description="E.g. B2B SaaS, API Usage-based, Open Source + Enterprise")
    funding_stage: Optional[str] = Field(None, description="E.g. Seed, Series A, Series B, Public, Bootstrapped")
    total_funding: Optional[str] = Field(None, description="Verified total funding amount e.g. $10M, $1B")
    latest_funding_round: Optional[str] = Field(None, description="Latest round identifier e.g. Series C")
    latest_funding_date: Optional[str] = Field(None, description="Latest funding date YYYY-MM-DD")
    investors: List[str] = Field(default_factory=list, description="Key venture capital or corporate investors")
    employee_range: Optional[str] = Field(None, description="Estimated employee range e.g. 11-50, 501-1000")
    founders: List[str] = Field(default_factory=list, description="Verified company founders")
    leadership: List[str] = Field(default_factory=list, description="Key executive leadership e.g. CEO, CTO")
    official_url: Optional[str] = Field(None, description="Official company website URL")
    linkedin_url: Optional[str] = Field(None, description="Official LinkedIn organization page")
    github_url: Optional[str] = Field(None, description="Official GitHub organization page")
    crunchbase_url: Optional[str] = Field(None, description="Crunchbase profile URL if available")
    tracxn_url: Optional[str] = Field(None, description="Tracxn profile URL if available")
    status: str = Field("ACTIVE", description="Operational status: ACTIVE, ACQUIRED, MERGED, CLOSED, INACTIVE, UNKNOWN")
    active: bool = Field(True, description="Whether currently active")
    acquisition_status: Optional[str] = Field(None, description="Details if acquired e.g. Acquired by Microsoft")
    parent_company: Optional[str] = Field(None, description="Parent organization if subsidiary")
    subsidiaries: List[str] = Field(default_factory=list, description="Subsidiary organizations")

    @field_validator("official_url", mode="before")
    @classmethod
    def validate_company_official_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        norm = normalize_url(v)
        return norm if norm else None

    @field_validator("github_url", mode="before")
    @classmethod
    def validate_company_github_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        norm = normalize_url(v)
        if norm.startswith("http://github.com"):
            norm = "https://github.com" + norm[17:]
        return norm.lower() if "github.com" in norm.lower() else norm

    @classmethod
    def create_canonical(cls, **kwargs) -> "CompanyRecord":
        """
        Creates a CompanyRecord with stable deterministic ID: company:<key>
        """
        name = (kwargs.get("name") or kwargs.get("company_name") or "").strip()
        official_url = kwargs.get("official_url") or kwargs.get("url") or ""
        github_url = kwargs.get("github_url") or ""

        domain = extract_domain(official_url) if official_url else ""
        clean_domain = domain.lower().replace("www.", "") if domain else ""

        if not kwargs.get("canonical_name"):
            kwargs["canonical_name"] = name.lower()

        # Deterministic ID key logic
        if clean_domain and "github.com" not in clean_domain:
            kwargs["id"] = f"company:{clean_domain}"
        elif github_url and "github.com/" in github_url.lower():
            clean_gh = github_url.lower().replace("https://github.com/", "").replace("http://github.com/", "").rstrip("/")
            kwargs["id"] = f"company:gh:{clean_gh}"
        else:
            clean_n = name.lower().replace(" ", "-").replace(",", "").replace(".", "")
            kwargs["id"] = f"company:{clean_n}"

        # Ensure primary URL field is set
        if not kwargs.get("url"):
            if official_url:
                kwargs["url"] = official_url
            elif github_url:
                kwargs["url"] = github_url
            else:
                clean_n = name.lower().replace(" ", "-")
                kwargs["url"] = f"https://ai-orbit.org/companies/{clean_n}"

        # Ensure discovery source
        if "discovery_source" not in kwargs:
            if "source" in kwargs and isinstance(kwargs["source"], DiscoverySource):
                kwargs["discovery_source"] = kwargs["source"]
            else:
                kwargs["discovery_source"] = DiscoverySource(
                    name=kwargs.pop("source_name", "GitHub Organizations & AI Directories"),
                    url=kwargs.get("url", ""),
                    source_type="API",
                    source_trust_level="HIGH"
                )
        if "source" not in kwargs:
            kwargs["source"] = kwargs["discovery_source"]

        return cls(**kwargs)
