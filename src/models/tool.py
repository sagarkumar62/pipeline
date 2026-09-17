from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator
from src.utils.urls import normalize_url, extract_domain
from src.utils.hashing import generate_tool_id


class DiscoverySource(BaseModel):
    """Where we discovered the candidate entity."""
    name: str = Field(..., description="Name of the discovery source (e.g., 'GitHub API', 'HuggingFace')")
    url: str = Field(..., description="URL where the candidate record was discovered")
    source_type: str = Field(default="UNKNOWN", description="E.g., CURATED_SEED, API, OFFICIAL_REGISTRY")
    source_trust_level: Literal["OFFICIAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"] = Field(
        default="UNKNOWN", description="Trust authority of the discovery source"
    )
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_data_ref: Optional[str] = Field(None, description="Path or reference identifier in raw storage")

    @field_validator("url", mode="before")
    @classmethod
    def validate_discovery_url(cls, v: str) -> str:
        return normalize_url(v) if v else ""


class SourceMetadata(DiscoverySource):
    """Backwards-compatible alias for DiscoverySource."""
    pass


class EvidenceSource(BaseModel):
    """The specific source/URL containing factual information supporting the entity."""
    url: str = Field(..., description="URL of the evidence document or repository")
    source_type: str = Field(..., description="E.g. OFFICIAL_WEBSITE, GITHUB_REPOSITORY, DOCUMENTATION, CURATED_SEED")
    trust_level: Literal["OFFICIAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"] = Field(default="UNKNOWN")
    evidence_type: str = Field(..., description="E.g. WEBSITE_PAGE, CODE_REPOSITORY, WEBSITE_META, SEED_CLAIM")

    @field_validator("url", mode="before")
    @classmethod
    def validate_evidence_url(cls, v: str) -> str:
        return normalize_url(v) if v else ""


class VerificationEvidence(BaseModel):
    """Audit trail for verification checks."""
    type: str = Field(..., description="E.g., SOURCE_CLAIM, DOMAIN_MATCH, HTTP_RESPONSE, REDIRECT, PAGE_TITLE, META")
    source: str = Field(..., description="Source of the evidence (e.g., 'Official Seed', 'HTTP Client')")
    value: str = Field(..., description="The value matched or observed")
    result: bool = Field(..., description="Whether this evidence supports identity verification")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VerificationResult(BaseModel):
    """Structured verification details distinguishing accessibility from identity."""
    http_status: Optional[int] = None
    accessible: bool = False
    verification_status: str = "UNKNOWN"
    identity_verified: Optional[bool] = None
    official_domain_match: bool = False
    title_match: Optional[bool] = None
    content_match: Optional[bool] = None
    redirect_verified: bool = False
    reason: Optional[str] = None
    canonical_domain: Optional[str] = None
    page_title: Optional[str] = None
    meta_description: Optional[str] = None
    verified_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    evidence: List[VerificationEvidence] = Field(default_factory=list)


class QualityMetrics(BaseModel):
    """Calculated quality scores for record audit."""
    source_validity: float = 1.0
    website_verification: float = 0.0
    logo_verification: float = 0.0
    description_quality: float = 0.0
    identity_confidence: float = 1.0
    metadata_completeness: float = 0.0
    composite_score: float = 0.0


class ToolRecord(BaseModel):
    """
    Canonical Pydantic model for a Tool entity in the AI Orbit Ecosystem.
    """
    id: str = Field(..., description="Deterministic stable Tool ID")
    entity_type: Literal["TOOL"] = "TOOL"
    name: str = Field(..., description="Primary display name of the tool")
    raw_name: Optional[str] = Field(None, description="Original raw name prior to cleaning")
    canonical_name: Optional[str] = Field(None, description="Normalized name used for deduplication")
    url: str = Field(..., description="Verified canonical website URL")
    official_url: Optional[str] = Field(None, description="Verified official canonical website URL of the tool")
    
    @field_validator("url", mode="before", check_fields=False)
    @classmethod
    def validate_tool_url(cls, v: str) -> str:
        return normalize_url(v) if v else ""

    @field_validator("official_url", mode="before", check_fields=False)
    @classmethod
    def validate_official_url(cls, v: Optional[str]) -> Optional[str]:
        return normalize_url(v) if v else None
    
    # Grounded Description
    description: Optional[str] = Field(None, description="Concise, factual 1-2 sentence description")
    description_source_type: Optional[str] = Field(None, description="E.g., OFFICIAL_WEBSITE, GITHUB_API, LLM_GROUNDED_*")
    description_source_url: Optional[str] = Field(None, description="URL where the fact was extracted")
    description_grounded: bool = Field(False, description="Whether the description is strictly grounded in evidence")
    description_generation_method: Optional[str] = Field(None, description="E.g., LLM_GEMINI, LLM_GROQ, EXTRACTED_FROM_SOURCE")
    llm_provider_used: Optional[str] = Field(None, description="Name of LLM provider used (e.g. Gemini, Groq, DeepSeek, NONE)")
    llm_enrichment_status: Optional[str] = Field("NOT_CONFIGURED", description="LLM enrichment status (SUCCESS, FAILED_FALLBACK_TO_SOURCE, NOT_CONFIGURED, DISABLED)")
    
    categories: List[str] = Field(default_factory=list, description="Assigned taxonomy categories")
    source: DiscoverySource = Field(..., description="Discovery source metadata")
    discovery_source: DiscoverySource = Field(..., description="Primary discovery source metadata")
    evidence_sources: List[EvidenceSource] = Field(default_factory=list, description="URLs containing factual evidence supporting candidate")
    external_evidence_available: bool = Field(False, description="Whether verified external evidence exists")
    external_evidence_url: Optional[str] = Field(None, description="Primary external evidence URL")

    # Verified Metadata
    logo_url: Optional[str] = Field(None, description="Verified official logo asset URL")
    logo_verified: bool = Field(False, description="Whether logo was actively verified")
    logo_found: bool = Field(False, description="Whether a logo was found at all")
    logo_access_blocked: bool = Field(False, description="Whether logo discovery was blocked by anti-bot")
    logo_source: Optional[str] = Field(None, description="Origin tag of logo (e.g. og:image, favicon)")
    
    company_name: Optional[str] = Field(None, description="Name of developing company/organization")
    company_url: Optional[str] = Field(None, description="Official URL of developing company")
    pricing_model: Optional[str] = Field(None, description="Pricing model (Free, Freemium, Paid, Open Source)")

    # GitHub metadata
    github_stars: Optional[int] = Field(None, description="GitHub stargazer count from API")
    github_repo_url: Optional[str] = Field(None, description="GitHub repository URL (distinct from official_url)")
    github_repository_verified: bool = Field(False, description="Whether GitHub repository evidence is verified")
    
    website_verified: bool = Field(False, description="True ONLY when an external official website is verified.")
    verification_status: str = Field("UNKNOWN", description="Detailed verification state (e.g., ACCESSIBLE_VERIFIED, ACCESS_BLOCKED)")
    verification_reason: Optional[str] = Field(None, description="Reason / details of verification result")
    verification_evidence: List[VerificationEvidence] = Field(default_factory=list)
    quality_score: float = Field(0.0, description="Audit and verification quality score")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of record creation")

    # Deduplication & Matching Metadata
    duplicate_of: Optional[str] = Field(None, description="Canonical ID if resolved as duplicate")

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
