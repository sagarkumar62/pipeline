from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator
from src.utils.urls import normalize_url, extract_domain


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


class EntityTimestamps(BaseModel):
    """Record lifecycle timestamps."""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None


class BaseEntity(BaseModel):
    """
    Abstract base entity model for all AI Orbit modules.
    Defines the 12 core common fields required across all modules.
    """
    id: str = Field(..., description="Deterministic stable entity ID")
    entity_type: str = Field(..., description="Entity type discriminator (TOOL, REPOSITORY, MCP, AGENT, MODEL, etc.)")
    name: str = Field(..., description="Primary display name of the entity")
    raw_name: Optional[str] = Field(None, description="Original raw name prior to cleaning")
    canonical_name: Optional[str] = Field(None, description="Normalized name used for deduplication")
    url: str = Field(..., description="Verified canonical primary URL")
    
    @field_validator("url", mode="before", check_fields=False)
    @classmethod
    def validate_entity_url(cls, v: str) -> str:
        return normalize_url(v) if v else ""

    description: Optional[str] = Field(None, description="Concise, factual 1-2 sentence description")
    description_source_type: Optional[str] = Field(None, description="E.g., OFFICIAL_WEBSITE, GITHUB_API, EXTRACTED_FROM_SOURCE")
    description_source_url: Optional[str] = Field(None, description="URL where the fact was extracted")
    description_grounded: bool = Field(False, description="Whether description is strictly grounded in evidence")
    description_generation_method: Optional[str] = Field(None, description="E.g., EXTRACTED_FROM_SOURCE, LLM_GEMINI")
    llm_provider_used: Optional[str] = Field(None, description="LLM provider name if used")
    llm_enrichment_status: Optional[str] = Field("NOT_CONFIGURED", description="LLM enrichment status")

    categories: List[str] = Field(default_factory=list, description="Assigned taxonomy categories")
    source: DiscoverySource = Field(..., description="Discovery source metadata")
    discovery_source: DiscoverySource = Field(..., description="Primary discovery source metadata")
    evidence_sources: List[EvidenceSource] = Field(default_factory=list, description="URLs containing factual evidence")
    external_evidence_available: bool = Field(False, description="Whether verified external evidence exists")
    external_evidence_url: Optional[str] = Field(None, description="Primary external evidence URL")

    # Verified Metadata
    logo_url: Optional[str] = Field(None, description="Verified official logo asset URL")
    logo_verified: bool = Field(False, description="Whether logo was actively verified")
    logo_found: bool = Field(False, description="Whether a logo was found at all")
    logo_access_blocked: bool = Field(False, description="Whether logo discovery was blocked by anti-bot")
    logo_source: Optional[str] = Field(None, description="Origin tag of logo (e.g. og:image, favicon)")

    website_verified: bool = Field(False, description="True ONLY when an external official website is verified.")
    verification_status: str = Field("UNKNOWN", description="Detailed verification state")
    verification_reason: Optional[str] = Field(None, description="Reason / details of verification result")
    verification_evidence: List[VerificationEvidence] = Field(default_factory=list)
    quality_score: float = Field(0.0, description="Audit and verification quality score")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    duplicate_of: Optional[str] = Field(None, description="Canonical ID if resolved as duplicate")
