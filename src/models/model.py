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


class ModelRecord(BaseEntity):
    """
    Canonical Pydantic model for an AI Model entity in the AI Orbit Ecosystem.
    Distinguished by entity_type='MODEL'.
    
    A Model represents a distinct base AI architecture, foundation model, or fine-tuned model release.
    Variants such as provider endpoints, hosting mirrors, and quantization formats are consolidated
    into metadata attributes of the canonical model rather than separate entity records.
    """
    entity_type: Literal["MODEL"] = "MODEL"

    # Model Specific Metadata Fields
    model_name: Optional[str] = Field(None, description="Primary model name e.g. Llama 3.1 8B Instruct")
    model_family: Optional[str] = Field(None, description="Model family series e.g. Llama, GPT, Claude, Mistral, Qwen, DeepSeek, Gemini")
    version: Optional[str] = Field(None, description="Specific release version e.g. 3.1, 4o, 3.5 Sonnet, 2.0")
    release_date: Optional[str] = Field(None, description="Official release date YYYY-MM-DD")
    model_type: Optional[str] = Field(None, description="E.g. Foundation Model, Large Language Model, Vision-Language Model, Embedding Model, Reasoning Model")
    architecture: Optional[str] = Field(None, description="Model architecture type e.g. Transformer, MoE, Diffusion, Mamba")
    modality: List[str] = Field(default_factory=list, description="Supported modalities e.g. text, image, audio, video, code")
    capabilities: List[str] = Field(default_factory=list, description="Model capabilities e.g. function_calling, vision, json_mode, code_execution")
    context_window: Optional[int] = Field(None, description="Maximum token context window size")
    parameter_count: Optional[str] = Field(None, description="Total parameters e.g. 8B, 70B, 405B, 1.5B")
    active_parameters: Optional[str] = Field(None, description="Active parameters for MoE models e.g. 39B active of 236B total")
    training_data: Optional[str] = Field(None, description="Training dataset details or token count")
    license: Optional[str] = Field(None, description="License terms e.g. Apache-2.0, Llama-3.1, MIT, Proprietary")
    open_source: bool = Field(True, description="Whether open-weights or open-source")
    weights_available: bool = Field(False, description="Whether downloadable model weights are publicly available")
    repository_url: Optional[str] = Field(None, description="Source code or model repository URL")
    huggingface_id: Optional[str] = Field(None, description="Hugging Face repository ID e.g. meta-llama/Llama-3.1-8B-Instruct")
    provider: Optional[str] = Field(None, description="Primary model creator/provider e.g. Meta, OpenAI, Anthropic, Mistral AI, Google, DeepSeek")
    providers: List[str] = Field(default_factory=list, description="List of hosting/cloud providers serving this model e.g. Together, Groq, Fireworks")
    api_available: bool = Field(True, description="Whether API endpoint access is provided")
    input_modalities: List[str] = Field(default_factory=list, description="Accepted input formats e.g. Text, Image, Audio")
    output_modalities: List[str] = Field(default_factory=list, description="Produced output formats e.g. Text, Image, Audio, Code")
    languages: List[str] = Field(default_factory=list, description="Supported human/programming languages")
    benchmark_evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Verified benchmark entries")
    deployment_type: Optional[str] = Field(None, description="Deployment tier e.g. API, Local Weights, Cloud Hosted")
    quantization: Optional[str] = Field(None, description="Quantization format if applicable e.g. GGUF, GPTQ, AWQ, FP16")
    base_model: Optional[str] = Field(None, description="Reference ID or name of base model if this record is a fine-tune")
    fine_tuned_from: Optional[str] = Field(None, description="Parent base model repository/name")
    official_url: Optional[str] = Field(None, description="Official project documentation or landing page")

    @field_validator("repository_url", mode="before")
    @classmethod
    def validate_model_repo_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        norm = normalize_url(v)
        if norm.startswith("http://github.com"):
            norm = "https://github.com" + norm[17:]
        return norm.lower() if "github.com" in norm.lower() else norm

    @field_validator("official_url", mode="before")
    @classmethod
    def validate_model_official_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        norm = normalize_url(v)
        return norm if norm else None

    @classmethod
    def create_canonical(cls, **kwargs) -> "ModelRecord":
        """
        Creates a ModelRecord with stable deterministic ID: model:<key>
        """
        name = (kwargs.get("name") or kwargs.get("model_name") or "").strip()
        provider = (kwargs.get("provider") or "").strip().lower()
        hf_id = (kwargs.get("huggingface_id") or "").strip().lower()
        repo_url = kwargs.get("repository_url") or kwargs.get("url") or ""

        if repo_url:
            repo_url = normalize_url(repo_url)
            kwargs["repository_url"] = repo_url
            kwargs["url"] = repo_url

        if not kwargs.get("canonical_name"):
            kwargs["canonical_name"] = name.lower()

        # Deterministic ID key logic
        if hf_id:
            clean_hf = hf_id.replace("/", "--").replace(" ", "-")
            kwargs["id"] = f"model:hf:{clean_hf}"
        elif repo_url and "github.com/" in repo_url.lower():
            clean = repo_url.lower().replace("https://github.com/", "").replace("http://github.com/", "").rstrip("/")
            kwargs["id"] = f"model:{clean}"
        elif provider and name:
            clean_p = provider.lower().replace(" ", "-")
            clean_n = name.lower().replace(" ", "-")
            kwargs["id"] = f"model:{clean_p}/{clean_n}"
        else:
            clean_n = name.lower().replace(" ", "-")
            kwargs["id"] = f"model:{clean_n}"

        # Ensure discovery source
        if "discovery_source" not in kwargs:
            if "source" in kwargs and isinstance(kwargs["source"], DiscoverySource):
                kwargs["discovery_source"] = kwargs["source"]
            else:
                kwargs["discovery_source"] = DiscoverySource(
                    name=kwargs.pop("source_name", "OpenRouter / HuggingFace API"),
                    url=kwargs.get("url", ""),
                    source_type="API",
                    source_trust_level="HIGH"
                )
        if "source" not in kwargs:
            kwargs["source"] = kwargs["discovery_source"]

        # Ensure url field is set
        if not kwargs.get("url"):
            if kwargs.get("official_url"):
                kwargs["url"] = kwargs["official_url"]
            elif kwargs.get("repository_url"):
                kwargs["url"] = kwargs["repository_url"]
            elif hf_id:
                kwargs["url"] = f"https://huggingface.co/{hf_id}"
            else:
                clean_n = name.lower().replace(" ", "-")
                kwargs["url"] = f"https://ai-orbit.org/models/{clean_n}"

        return cls(**kwargs)
