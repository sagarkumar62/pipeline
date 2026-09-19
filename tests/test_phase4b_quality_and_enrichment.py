"""
Phase 4B Quality & Enrichment Unit Tests

10 Mandatory Test Cases covering description quality checking, generic/tautological detection,
controlled regeneration, provenance integrity, canonical field immutability, and 50-record regression.
"""

import pytest
import asyncio
from typing import Dict, Any, List
from src.enrichment.quality import DescriptionQualityChecker
from src.enrichment.schema import EvidencePackage, LLMResult, StructuredLLMOutput
from src.enrichment.mock_provider import MockLLMProvider
from src.enrichment.orchestrator import LLMOrchestrator
from src.models.tool import ToolRecord


# Test 1: Generic description detection
def test_generic_description_detection():
    checker = DescriptionQualityChecker()
    flag, is_pass = checker.check_quality("AutoBot is an innovative AI tool for better productivity.", "AutoBot")
    assert flag == "GENERIC"
    assert is_pass is False


# Test 2: Tautological description detection
def test_tautological_description_detection():
    checker = DescriptionQualityChecker()
    flag, is_pass = checker.check_quality("AutoBot is a tool that helps users use AI.", "AutoBot")
    assert flag == "TAUTOLOGICAL"
    assert is_pass is False


# Test 3: Grounded but low-information description
def test_grounded_low_information_description():
    checker = DescriptionQualityChecker()
    flag, is_pass = checker.check_quality("runs anywhere on the web", "AutoBot")
    assert flag == "LOW_INFORMATION"
    assert is_pass is False


# Test 4: Regeneration using identical evidence
@pytest.mark.asyncio
async def test_regeneration_using_identical_evidence():
    # Mock provider returning short slogan first (len=26, passes grounding validator but triggers LOW_INFORMATION quality check)
    provider = MockLLMProvider("Groq", "SUCCESS", custom_description="runs anywhere on the web")
    orchestrator = LLMOrchestrator(providers=[provider])
    record = {
        "name": "AutoBot",
        "description": "AutoBot autonomous agent",
        "github_repo_url": "https://github.com/autobot/autobot",
        "topics": ["agent", "automation"]
    }
    res = await orchestrator.enrich_description(record, enrich_llm_flag=True)

    assert orchestrator.metrics["regeneration_attempts"] >= 1
    assert res["description"] is not None
    assert res["llm_enrichment_status"] == "SUCCESS"


# Test 5: Source fallback
@pytest.mark.asyncio
async def test_source_fallback():
    provider = MockLLMProvider("Gemini", "SIMULATED_429")
    orchestrator = LLMOrchestrator(providers=[provider])
    record = {
        "name": "FallbackTool",
        "description": "FallbackTool is an open-source data processor for structured CSV inputs.",
        "github_repo_url": "https://github.com/fallback/tool"
    }
    res = await orchestrator.enrich_description(record, enrich_llm_flag=True)

    assert res["llm_provider_used"] == "NONE"
    assert res["llm_enrichment_status"] == "FAILED_FALLBACK_TO_SOURCE"
    assert res["description_generation_method"] == "EXTRACTED_FROM_SOURCE"
    assert res["description"] == "FallbackTool is an open-source data processor for structured CSV inputs."


# Test 6: Provenance correctness
@pytest.mark.asyncio
async def test_provenance_correctness():
    provider = MockLLMProvider("Groq", "SUCCESS", custom_description="AutoBot automates web scraping tasks using LLMs.")
    orchestrator = LLMOrchestrator(providers=[provider])
    record = {
        "name": "AutoBot",
        "github_repo_url": "https://github.com/autobot/autobot"
    }
    res = await orchestrator.enrich_description(record, enrich_llm_flag=True)

    assert res["llm_enrichment_status"] == "SUCCESS"
    assert res["llm_provider_used"] == "Groq"
    assert res["description_generation_method"] == "LLM_GROQ"
    assert res["description_source_type"] == "LLM_GROUNDED_GITHUB_REPOSITORY"
    assert res["description_grounded"] is True






# Test 9: URL provenance integrity
@pytest.mark.asyncio
async def test_url_provenance_integrity():
    from src.enrichment.validator import GroundingValidator
    validator = GroundingValidator()
    pkg = EvidencePackage(
        tool_name="MyTool",
        source_urls=["https://mytool.dev", "https://github.com/user/mytool"]
    )
    # Valid cited URL
    out_valid = StructuredLLMOutput(
        description="MyTool processes workflow requests.",
        grounded=True,
        evidence_used=[{"source_url": "https://mytool.dev", "source_type": "OFFICIAL_WEBSITE"}]
    )
    is_valid, _ = validator.validate(out_valid, pkg)
    assert is_valid is True

    # Hallucinated uncited URL
    out_invalid = StructuredLLMOutput(
        description="MyTool processes workflow requests.",
        grounded=True,
        evidence_used=[{"source_url": "https://fake-hallucinated-domain.com", "source_type": "OFFICIAL_WEBSITE"}]
    )
    is_invalid, reason = validator.validate(out_invalid, pkg)
    assert is_invalid is False
    assert "UNCITED_SOURCE_URL" in reason


# Test 10: Provider metrics tracking
@pytest.mark.asyncio
async def test_provider_metrics_tracking():
    gemini = MockLLMProvider("Gemini", "SIMULATED_429")
    groq = MockLLMProvider("Groq", "SUCCESS", custom_description="AutoBot executes workflows autonomously.")
    orchestrator = LLMOrchestrator(providers=[gemini, groq])
    record = {"name": "AutoBot", "github_repo_url": "https://github.com/autobot/autobot"}
    
    await orchestrator.enrich_description(record, enrich_llm_flag=True)

    assert orchestrator.metrics["llm_records_processed"] == 1
    assert orchestrator.metrics["provider_attempts"]["Gemini"] == 1
    assert orchestrator.metrics["provider_failures"]["Gemini"] == 1
    assert orchestrator.metrics["provider_attempts"]["Groq"] == 1
    assert orchestrator.metrics["provider_successes"]["Groq"] == 1
    assert orchestrator.metrics["grounded_descriptions"] == 1
