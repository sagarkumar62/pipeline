"""
Phase 4 Mock LLM Provider for Unit Testing and Fallback Demonstrations

Supports configurable simulation modes: SUCCESS, SIMULATED_429, SIMULATED_TIMEOUT,
SIMULATED_AUTH_ERROR, SIMULATED_MALFORMED, SIMULATED_UNGROUNDED, SIMULATED_UNSUPPORTED_URL.
"""

from typing import Optional, Dict, Any
from src.enrichment.llm_base import BaseLLMProvider
from src.enrichment.schema import EvidencePackage, LLMResult
from src.utils.logging import setup_logger

logger = setup_logger("mock_llm_provider")


class MockLLMProvider(BaseLLMProvider):
    """Deterministic mock provider for unit testing without live API keys."""

    def __init__(
        self,
        name: str = "Mock",
        mode: str = "SUCCESS",
        custom_description: Optional[str] = None,
        custom_evidence_url: Optional[str] = None,
    ):
        super().__init__()
        self._name = name
        self.mode = mode
        self.custom_description = custom_description
        self.custom_evidence_url = custom_evidence_url

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def is_available(self) -> bool:
        return not self.auth_failed

    async def generate_description(self, evidence: EvidencePackage) -> LLMResult:
        if self.auth_failed or self.mode == "SIMULATED_AUTH_ERROR":
            self.auth_failed = True
            logger.warning(f"MockProvider {self.provider_name}: Simulated 401/403 Authentication Error.")
            return LLMResult(
                provider_name=self.provider_name,
                status="AUTH_ERROR",
                error_message="HTTP 401 Unauthorized",
                latency_ms=10.0,
            )

        if self.mode == "SIMULATED_429":
            logger.warning(f"MockProvider {self.provider_name}: Simulated 429 Rate Limit Exceeded.")
            return LLMResult(
                provider_name=self.provider_name,
                status="RATE_LIMITED",
                error_message="HTTP 429 Too Many Requests",
                latency_ms=15.0,
            )

        if self.mode == "SIMULATED_TIMEOUT":
            logger.warning(f"MockProvider {self.provider_name}: Simulated Connection Timeout.")
            return LLMResult(
                provider_name=self.provider_name,
                status="TIMEOUT",
                error_message="Connection timeout after 10.0s",
                latency_ms=10000.0,
            )

        if self.mode == "SIMULATED_MALFORMED":
            logger.warning(f"MockProvider {self.provider_name}: Simulated Malformed JSON Output.")
            return LLMResult(
                provider_name=self.provider_name,
                status="MALFORMED",
                error_message="Invalid JSON response from LLM",
                latency_ms=50.0,
            )

        if self.mode == "SIMULATED_UNGROUNDED":
            desc = self.custom_description or f"{evidence.tool_name} costs $99 per month and has 1 million active users."
            logger.warning(f"MockProvider {self.provider_name}: Simulated Ungrounded Output.")
            return LLMResult(
                description=desc,
                grounded=False,
                confidence="low",
                evidence_used=[],
                provider_name=self.provider_name,
                status="UNGROUNDED",
                error_message="Model returned ungrounded/hallucinated claims",
                latency_ms=100.0,
            )

        if self.mode == "SIMULATED_UNSUPPORTED_URL":
            cited_url = self.custom_evidence_url or "https://hallucinated-fake-url.com/docs"
            return LLMResult(
                description=f"{evidence.tool_name} is an open-source tool built for developers.",
                grounded=True,
                confidence="high",
                evidence_used=[{"source_url": cited_url, "source_type": "WEBSITE_PAGE"}],
                provider_name=self.provider_name,
                status="SUCCESS",
                latency_ms=80.0,
            )

        # SUCCESS mode
        cited_url = evidence.source_urls[0] if evidence.source_urls else "https://github.com/example/repo"
        desc = (
            self.custom_description
            if self.custom_description is not None
            else f"{evidence.tool_name} is a tool that assists developers with autonomous workflow automation."
        )

        if not desc or len(desc.strip()) == 0:
            return LLMResult(
                description=None,
                grounded=False,
                confidence="low",
                evidence_used=[],
                provider_name=self.provider_name,
                status="MALFORMED",
                error_message="Empty description returned by LLM",
                latency_ms=80.0,
            )

        return LLMResult(
            description=desc,
            grounded=True,
            confidence="high",
            evidence_used=[{"source_url": cited_url, "source_type": "GITHUB_REPOSITORY"}],
            provider_name=self.provider_name,
            status="SUCCESS",
            latency_ms=120.0,
        )
