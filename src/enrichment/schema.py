"""
Phase 4 LLM Orchestration Data Models and Schemas

Defines evidence packaging, structured LLM JSON outputs, and provider result objects.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class EvidencePackage(BaseModel):
    """Structured evidence package constructed from collected pipeline evidence."""
    tool_name: str
    official_website_content: Optional[str] = None
    official_website_url: Optional[str] = None
    repository_description: Optional[str] = None
    github_repo_url: Optional[str] = None
    readme_excerpt: Optional[str] = None
    readme_url: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    company_name: Optional[str] = None
    source_urls: List[str] = Field(default_factory=list)
    truncated: bool = False


class EvidenceUsed(BaseModel):
    """Source evidence reference cited in structured LLM output."""
    source_url: str
    source_type: str


class StructuredLLMOutput(BaseModel):
    """Structured machine-readable output required from LLM generation."""
    description: Optional[str] = None
    grounded: bool = False
    confidence: str = "low"  # "high", "medium", "low"
    evidence_used: List[EvidenceUsed] = Field(default_factory=list)


class LLMResult(BaseModel):
    """Normalized provider response object passed from LLMProviders to LLMOrchestrator."""
    description: Optional[str] = None
    grounded: bool = False
    confidence: str = "low"
    evidence_used: List[Dict[str, str]] = Field(default_factory=list)
    provider_name: str = "UNKNOWN"
    status: str = "FAILED"  # SUCCESS, FALLBACK, MALFORMED, UNGROUNDED, AUTH_ERROR, RATE_LIMITED, TIMEOUT, ERROR
    error_message: Optional[str] = None
    latency_ms: float = 0.0
    source_type: str = "SOURCE_DERIVED"
