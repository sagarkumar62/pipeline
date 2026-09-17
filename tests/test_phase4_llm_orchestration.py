"""
Phase 4 LLM Orchestration Unit Tests

14 Mandatory Test Cases covering provider fallback, error handling, rate limits,
auth failure, malformed JSON, grounding validation, and evidence packaging.
"""

import pytest
import asyncio
from typing import Dict, Any
from src.enrichment.schema import EvidencePackage, LLMResult, StructuredLLMOutput
from src.enrichment.mock_provider import MockLLMProvider
from src.enrichment.orchestrator import LLMOrchestrator
from src.enrichment.validator import GroundingValidator


@pytest.fixture
def sample_record() -> Dict[str, Any]:
    return {
        "name": "AutoBot",
        "description": "AutoBot is an autonomous agent framework for browser automation.",
        "official_url": "https://autobot.dev",
        "github_repo_url": "https://github.com/autobot/autobot",
        "topics": ["ai", "automation", "agent"],
        "readme_content": "AutoBot is an open-source framework designed for AI agent browser execution.",
        "website_verified": True,
        "evidence_sources": [
            {"url": "https://autobot.dev", "source_type": "OFFICIAL_WEBSITE", "trust_level": "OFFICIAL", "evidence_type": "WEBSITE_PAGE"},
            {"url": "https://github.com/autobot/autobot", "source_type": "GITHUB_REPOSITORY", "trust_level": "HIGH", "evidence_type": "CODE_REPOSITORY"}
        ]
    }


# Test 1: Gemini success
@pytest.mark.asyncio
async def test_gemini_success(sample_record):
    gemini = MockLLMProvider("Gemini", "SUCCESS", "AutoBot automates web interactions using autonomous AI agents.")
    orchestrator = LLMOrchestrator(providers=[gemini])
    res = await orchestrator.enrich_description(sample_record, enrich_llm_flag=True)

    assert res["description"] == "AutoBot automates web interactions using autonomous AI agents."
    assert res["description_grounded"] is True
    assert res["llm_provider_used"] == "Gemini"
    assert res["llm_enrichment_status"] == "SUCCESS"


# Test 2: Gemini timeout -> Groq fallback
@pytest.mark.asyncio
async def test_gemini_timeout_fallback(sample_record):
    gemini = MockLLMProvider("Gemini", "SIMULATED_TIMEOUT")
    groq = MockLLMProvider("Groq", "SUCCESS", "AutoBot runs web tasks autonomously.")
    orchestrator = LLMOrchestrator(providers=[gemini, groq])
    res = await orchestrator.enrich_description(sample_record, enrich_llm_flag=True)

    assert res["description"] == "AutoBot runs web tasks autonomously."
    assert res["llm_provider_used"] == "Groq"
    assert res["llm_enrichment_status"] == "SUCCESS"


# Test 3: Gemini 429 -> retry/fallback
@pytest.mark.asyncio
async def test_gemini_429_retry_or_fallback(sample_record):
    gemini = MockLLMProvider("Gemini", "SIMULATED_429")
    groq = MockLLMProvider("Groq", "SUCCESS", "AutoBot handles web tasks.")
    orchestrator = LLMOrchestrator(providers=[gemini, groq])
    res = await orchestrator.enrich_description(sample_record, enrich_llm_flag=True)

    assert res["llm_provider_used"] == "Groq"
    assert res["llm_enrichment_status"] == "SUCCESS"


# Test 4: Gemini auth failure -> fallback without repeated retries
@pytest.mark.asyncio
async def test_gemini_auth_failure_no_repeat(sample_record):
    gemini = MockLLMProvider("Gemini", "SIMULATED_AUTH_ERROR")
    groq = MockLLMProvider("Groq", "SUCCESS", "AutoBot automates workflows.")
    orchestrator = LLMOrchestrator(providers=[gemini, groq])
    
    assert gemini.auth_failed is False
    res = await orchestrator.enrich_description(sample_record, enrich_llm_flag=True)
    
    assert gemini.auth_failed is True
    assert gemini.is_available is False
    assert res["llm_provider_used"] == "Groq"


# Test 5: Groq success
@pytest.mark.asyncio
async def test_groq_success(sample_record):
    groq = MockLLMProvider("Groq", "SUCCESS", "AutoBot provides browser agent automation.")
    orchestrator = LLMOrchestrator(providers=[groq])
    res = await orchestrator.enrich_description(sample_record, enrich_llm_flag=True)

    assert res["llm_provider_used"] == "Groq"
    assert res["llm_enrichment_status"] == "SUCCESS"


# Test 6: Groq failure -> DeepSeek fallback
@pytest.mark.asyncio
async def test_groq_failure_deepseek_fallback(sample_record):
    gemini = MockLLMProvider("Gemini", "SIMULATED_TIMEOUT")
    groq = MockLLMProvider("Groq", "SIMULATED_MALFORMED")
    deepseek = MockLLMProvider("DeepSeek", "SUCCESS", "AutoBot executes browser tasks.")
    orchestrator = LLMOrchestrator(providers=[gemini, groq, deepseek])
    res = await orchestrator.enrich_description(sample_record, enrich_llm_flag=True)

    assert res["llm_provider_used"] == "DeepSeek"
    assert res["llm_enrichment_status"] == "SUCCESS"


# Test 7: All providers unavailable
@pytest.mark.asyncio
async def test_all_providers_unavailable(sample_record):
    gemini = MockLLMProvider("Gemini", "SIMULATED_AUTH_ERROR")
    groq = MockLLMProvider("Groq", "SIMULATED_TIMEOUT")
    deepseek = MockLLMProvider("DeepSeek", "SIMULATED_429")
    orchestrator = LLMOrchestrator(providers=[gemini, groq, deepseek])
    res = await orchestrator.enrich_description(sample_record, enrich_llm_flag=True)

    assert res["llm_provider_used"] == "NONE"
    assert res["llm_enrichment_status"] == "FAILED_FALLBACK_TO_SOURCE"
    assert res["description_source_type"] in ["SOURCE_DERIVED", "GITHUB_REPOSITORY_DESCRIPTION", "OFFICIAL_WEBSITE", "GITHUB_README"]


# Test 8: Malformed LLM response
@pytest.mark.asyncio
async def test_malformed_llm_response(sample_record):
    gemini = MockLLMProvider("Gemini", "SIMULATED_MALFORMED")
    orchestrator = LLMOrchestrator(providers=[gemini])
    res = await orchestrator.enrich_description(sample_record, enrich_llm_flag=True)

    assert res["llm_enrichment_status"] == "FAILED_FALLBACK_TO_SOURCE"
    assert orchestrator.metrics["malformed_responses"] == 1


# Test 9: Empty description
@pytest.mark.asyncio
async def test_empty_description(sample_record):
    gemini = MockLLMProvider("Gemini", "SUCCESS", custom_description="")
    orchestrator = LLMOrchestrator(providers=[gemini])
    res = await orchestrator.enrich_description(sample_record, enrich_llm_flag=True)

    assert res["llm_enrichment_status"] == "FAILED_FALLBACK_TO_SOURCE"


# Test 10: Unsupported claim / grounding failure
@pytest.mark.asyncio
async def test_unsupported_claim_grounding_failure(sample_record):
    gemini = MockLLMProvider("Gemini", "SIMULATED_UNGROUNDED")
    orchestrator = LLMOrchestrator(providers=[gemini])
    res = await orchestrator.enrich_description(sample_record, enrich_llm_flag=True)

    assert res["llm_enrichment_status"] == "FAILED_FALLBACK_TO_SOURCE"
    assert orchestrator.metrics["ungrounded_responses"] == 1


# Test 11: Valid grounded description
@pytest.mark.asyncio
async def test_valid_grounded_description(sample_record):
    validator = GroundingValidator()
    pkg = EvidencePackage(
        tool_name="AutoBot",
        repository_description="AutoBot is an autonomous agent framework for browser automation.",
        source_urls=["https://github.com/autobot/autobot"]
    )
    out = StructuredLLMOutput(
        description="AutoBot is an autonomous agent framework for browser automation.",
        grounded=True,
        confidence="high",
        evidence_used=[{"source_url": "https://github.com/autobot/autobot", "source_type": "GITHUB_REPOSITORY"}]
    )
    is_valid, reason = validator.validate(out, pkg)
    assert is_valid is True
    assert reason == "VALID_GROUNDED"


# Test 12: Evidence URL not present in evidence package
@pytest.mark.asyncio
async def test_uncited_evidence_url_failure(sample_record):
    gemini = MockLLMProvider("Gemini", "SIMULATED_UNSUPPORTED_URL")
    orchestrator = LLMOrchestrator(providers=[gemini])
    res = await orchestrator.enrich_description(sample_record, enrich_llm_flag=True)

    assert res["llm_enrichment_status"] == "FAILED_FALLBACK_TO_SOURCE"


# Test 13: Oversized README truncation
def test_oversized_readme_truncation(sample_record):
    sample_record["readme_content"] = "A" * 5000
    orchestrator = LLMOrchestrator(providers=[])
    pkg = orchestrator.construct_evidence_package(sample_record, max_chars=1000)

    assert pkg.truncated is True
    assert len(pkg.readme_excerpt) < 1500
    assert pkg.readme_excerpt.endswith("...[TRUNCATED]")


# Test 14: Provider response normalization
@pytest.mark.asyncio
async def test_provider_response_normalization(sample_record):
    mock = MockLLMProvider("Mock", "SUCCESS", "Sample normalized description.")
    pkg = EvidencePackage(tool_name="AutoBot", source_urls=["https://autobot.dev"])
    res: LLMResult = await mock.generate_description(pkg)

    assert isinstance(res, LLMResult)
    assert res.provider_name == "Mock"
    assert res.status == "SUCCESS"
    assert res.grounded is True
    assert res.description == "Sample normalized description."
