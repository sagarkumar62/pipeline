from datetime import datetime, timezone
import hashlib
from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field, field_validator
from src.utils.urls import normalize_url, extract_domain
from src.models.base import BaseEntity, DiscoverySource


class NewsSource(BaseModel):
    """Source definition for the News Source Registry."""
    source_id: str = Field(..., description="Unique identifier for the source")
    source_name: str = Field(..., description="Display name of the news source/publisher")
    source_type: str = Field(..., description="E.g. RSS_FEED, ATOM_FEED, OFFICIAL_API, SITEMAP")
    feed_url: str = Field(..., description="URL of the RSS feed, API, or sitemap")
    publisher_domain: str = Field(..., description="Primary domain of publisher e.g. arxiv.org, technologyreview.com")
    status: str = Field(default="ACTIVE", description="Status of feed e.g. ACTIVE, INACTIVE, DEPRECATED")
    last_checked: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    retrieval_method: str = Field(default="HTTP_GET", description="Method used to fetch feed")
    notes: Optional[str] = None


class NewsRecord(BaseEntity):
    """
    Canonical Pydantic model for a News entity in the AI Orbit Ecosystem.
    Distinguished by entity_type='news'.
    """
    entity_type: Literal["news"] = "news"

    url: str = Field("", description="Verified canonical primary URL")
    title: str = Field(..., description="Original article headline")
    canonical_title: str = Field(..., description="Normalized article headline for deduplication")
    source_name: str = Field(..., description="Name of news publisher/source")
    source_domain: str = Field(..., description="Domain of publisher e.g. technologyreview.com")
    source_url: str = Field(..., description="Original source link URL")
    canonical_url: str = Field(..., description="Normalized canonical article link URL")

    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Article publication timestamp")
    updated_at: Optional[datetime] = Field(None, description="Article last update timestamp if available")
    author: Optional[str] = Field(None, description="Article author name if available")
    summary: str = Field("", description="Article summary or short excerpt")
    content_excerpt: Optional[str] = Field(None, description="Cleaned content excerpt if legitimately available")

    categories: List[str] = Field(default_factory=list, description="Categorized AI news taxonomy e.g. AI Models, Hardware, Research")
    entities: List[str] = Field(default_factory=list, description="Extracted named entities e.g. OpenAI, NVIDIA, GPT-4")
    topics: List[str] = Field(default_factory=list, description="Relevant topic tags")
    tags: List[str] = Field(default_factory=list, description="Source tags or keywords")

    image_url: Optional[str] = Field(None, description="Associated image URL if available")
    language: str = Field(default="en", description="Article language code")
    country: Optional[str] = Field(None, description="Country/region of publisher or topic")

    article_type: str = Field(default="NEWS_ARTICLE", description="Article classification e.g. NEWS_ARTICLE, RESEARCH_PAPER, BLOG_POST, PRESS_RELEASE")
    status: str = Field(default="QUALIFIED", description="Qualification status e.g. QUALIFIED, REVIEW_REQUIRED, REJECTED")

    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when article was scraped/ingested")
    last_verified: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when article was verified")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Audit trail provenance mapping")

    content_hash: str = Field(..., description="SHA-256 fingerprint of canonical title and summary")
    canonical_url_hash: str = Field(..., description="SHA-256 hash of canonical URL")
    event_cluster_id: Optional[str] = Field(None, description="Assigned event cluster ID if grouped")

    @field_validator("canonical_url", mode="before")
    @classmethod
    def validate_news_canonical_url(cls, v: Optional[str]) -> str:
        if not v:
            return ""
        norm = normalize_url(v)
        return norm if norm else v.strip()

    @classmethod
    def compute_canonical_url_hash(cls, url: str) -> str:
        norm = normalize_url(url) or url.strip().lower()
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()

    @classmethod
    def compute_content_hash(cls, canonical_title: str, summary: str) -> str:
        raw_text = f"{canonical_title.strip().lower()}|{summary.strip().lower()}"
        return hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
