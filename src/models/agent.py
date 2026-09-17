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


class AgentRecord(BaseEntity):
    """
    Canonical Pydantic model for an Agent entity in the AI Orbit Ecosystem.
    Distinguished by entity_type='AGENT'.
    
    An Agent is an AI system/application that can perform multi-step actions toward a goal,
    use tools or external systems, maintain state/context where applicable, and/or autonomously
    execute a workflow.
    """
    entity_type: Literal["AGENT"] = "AGENT"

    # Agent Specific Metadata Fields
    agent_type: Optional[str] = Field(
        None, description="E.g. Autonomous Agent, AI Assistant, Coding Agent, Research Agent, Browser Agent, Agent Framework, Agent Platform, Multi-Agent System"
    )
    agent_framework: Optional[str] = Field(None, description="Underlying framework e.g. LangChain, AutoGen, CrewAI, LlamaIndex, Custom")
    agent_platform: Optional[str] = Field(None, description="Hosting or execution platform e.g. LangGraph Cloud, E2B, Modal, Self-Hosted")
    capabilities: List[str] = Field(default_factory=list, description="Capabilities e.g. tool_use, planning, memory, multi_step, browser_automation")
    goals: List[str] = Field(default_factory=list, description="Target agent goals or domain tasks")
    tools_used: List[str] = Field(default_factory=list, description="Tools or integrations utilized e.g. WebSearch, CodeInterpreter, FileSystem")
    integrations: List[str] = Field(default_factory=list, description="Supported third-party integrations")
    supported_models: List[str] = Field(default_factory=list, description="LLMs supported e.g. GPT-4o, Claude 3.5 Sonnet, Llama 3")
    supported_platforms: List[str] = Field(default_factory=list, description="Target OS or platforms e.g. Web, CLI, Docker, Desktop")
    inputs: List[str] = Field(default_factory=list, description="Accepted input modalities e.g. Text, Voice, Image, API Call")
    outputs: List[str] = Field(default_factory=list, description="Produced output modalities e.g. Code, Text, Actions, Structured JSON")
    memory: Optional[str] = Field(None, description="Memory mechanism e.g. Episodic, Vector DB, Short-Term, Conversation Buffer")
    planning: Optional[str] = Field(None, description="Planning paradigm e.g. ReAct, Plan-and-Execute, Tree-of-Thoughts, None")
    tool_use: bool = Field(False, description="Whether agent explicitly invokes external tools")
    autonomy_level: Optional[str] = Field(None, description="Autonomy level e.g. Fully Autonomous, Semi-Autonomous, Human-in-the-Loop")
    human_in_loop: bool = Field(False, description="Whether human approval or interaction is required")
    deployment_type: Optional[str] = Field(None, description="Deployment target e.g. Cloud API, Local CLI, Desktop App, Web UI")
    authentication: Optional[str] = Field(None, description="Authentication mechanism e.g. API Key, OAuth, None")
    api_available: bool = Field(False, description="Whether API access is provided")
    open_source: bool = Field(True, description="Whether open-source")
    license: Optional[str] = Field(None, description="License type e.g. MIT, Apache-2.0")
    maintainer: Optional[str] = Field(None, description="Maintainer username or organization")
    language: Optional[str] = Field(None, description="Implementation language e.g. Python, TypeScript")
    repository_url: Optional[str] = Field(None, description="Source code repository URL")
    official_url: Optional[str] = Field(None, description="Official project documentation or landing page")

    @field_validator("repository_url", mode="before")
    @classmethod
    def validate_agent_repo_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        norm = normalize_url(v)
        if norm.startswith("http://github.com"):
            norm = "https://github.com" + norm[17:]
        return norm.lower() if "github.com" in norm.lower() else norm

    @field_validator("official_url", mode="before")
    @classmethod
    def validate_agent_official_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        norm = normalize_url(v)
        return norm if norm else None

    @classmethod
    def create_canonical(cls, **kwargs) -> "AgentRecord":
        """
        Creates an AgentRecord with stable deterministic ID: agent:<key>
        """
        name = (kwargs.get("name") or "").strip()
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
            kwargs["id"] = f"agent:{clean}"
        elif maintainer and name:
            clean_m = maintainer.lower()
            clean_n = name.lower().replace(" ", "-")
            kwargs["id"] = f"agent:{clean_m}/{clean_n}"
        else:
            clean_n = name.lower().replace(" ", "-")
            kwargs["id"] = f"agent:{clean_n}"

        # Ensure discovery source
        if "discovery_source" not in kwargs:
            if "source" in kwargs and isinstance(kwargs["source"], DiscoverySource):
                kwargs["discovery_source"] = kwargs["source"]
            else:
                kwargs["discovery_source"] = DiscoverySource(
                    name=kwargs.pop("source_name", "GitHub Agent Search"),
                    url=kwargs.get("url", ""),
                    source_type="API",
                    source_trust_level="HIGH"
                )
        if "source" not in kwargs:
            kwargs["source"] = kwargs["discovery_source"]

        return cls(**kwargs)
