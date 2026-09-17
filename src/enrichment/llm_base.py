"""
Phase 4 Base LLM Provider Interface

Abstract base class for all LLM providers in the fallback chain.
"""

from abc import ABC, abstractmethod
from typing import Optional
from src.enrichment.schema import EvidencePackage, LLMResult


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self):
        self.auth_failed: bool = False

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., Gemini, Groq, DeepSeek, Mock)."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if provider credentials/key are configured and valid."""
        pass

    @abstractmethod
    async def generate_description(self, evidence: EvidencePackage) -> LLMResult:
        """
        Generates a concise 1-2 sentence description strictly using provided evidence package.
        Returns a normalized LLMResult object.
        """
        pass
