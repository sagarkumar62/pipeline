import pytest
from src.models.tool import ToolRecord, DiscoverySource, EvidenceSource, VerificationResult, VerificationEvidence
from src.validation.validator import ValidationGate
from src.discovery.tool_discovery import SeedToolDiscovery, GitHubToolDiscovery
from src.extraction.tool_extractor import ToolExtractor
from src.normalization.normalizer import ToolNormalizer


def test_external_discovery_url_preserved():
    disc = DiscoverySource(
        name="GitHub API",
        url="https://api.github.com/search/repositories",
        source_type="API",
        source_trust_level="HIGH"
    )
    record = ToolRecord.create_canonical(
        name="LangChain",
        url="https://langchain.com",
        official_url="https://langchain.com",
        discovery_source=disc,
        description="Framework for developing applications powered by LLMs.",
        categories=["Developer Tools"]
    )
    assert record.discovery_source.url == "https://api.github.com/search/repositories"
    assert record.discovery_source.name == "GitHub API"
    assert record.discovery_source.source_type == "API"
    assert record.discovery_source.source_trust_level == "HIGH"


def test_external_evidence_url_preserved():
    evidence = EvidenceSource(
        url="https://github.com/langchain-ai/langchain",
        source_type="GITHUB_REPOSITORY",
        trust_level="HIGH",
        evidence_type="CODE_REPOSITORY"
    )
    record = ToolRecord.create_canonical(
        name="LangChain",
        url="https://langchain.com",
        official_url="https://langchain.com",
        source_name="GitHub API",
        source_url="https://api.github.com",
        source_type="API",
        source_trust_level="HIGH",
        description="Framework for developing applications powered by LLMs.",
        categories=["Developer Tools"]
    )
    record.evidence_sources.append(evidence)
    record.external_evidence_available = True
    record.external_evidence_url = "https://github.com/langchain-ai/langchain"

    assert record.external_evidence_available is True
    assert record.external_evidence_url == "https://github.com/langchain-ai/langchain"
    assert len(record.evidence_sources) == 1
    assert record.evidence_sources[0].url == "https://github.com/langchain-ai/langchain"


def test_discovery_url_differs_from_official_url():
    disc = DiscoverySource(
        name="GitHub API",
        url="https://api.github.com/search/repositories",
        source_type="API",
        source_trust_level="HIGH"
    )
    record = ToolRecord.create_canonical(
        name="FastAPI",
        url="https://fastapi.tiangolo.com",
        official_url="https://fastapi.tiangolo.com",
        discovery_source=disc,
        description="Modern, fast web framework for building APIs with Python.",
        categories=["Developer Tools"]
    )
    assert record.discovery_source.url != record.official_url
    assert record.discovery_source.url == "https://api.github.com/search/repositories"
    assert record.official_url == "https://fastapi.tiangolo.com"


def test_missing_external_evidence_correctly_flagged():
    extractor = ToolExtractor()
    normalizer = ToolNormalizer()
    
    raw_item = {
        "name": "ChatGPT",
        "url": "https://chatgpt.com",
        "official_url": "https://chatgpt.com",
        "discovery_source_name": "Official AI Directory Seed",
        "discovery_source_url": "internal://seed_tools",
        "discovery_source_type": "CURATED_SEED",
        "discovery_source_trust_level": "MEDIUM",
        "external_evidence_available": False,
        "external_evidence_url": None,
        "description": "Conversational AI assistant powered by OpenAI GPT-4o models.",
        "category": "AI Assistants"
    }

    extracted = extractor.extract(raw_item, "Official AI Directory Seed")
    assert extracted["external_evidence_available"] is False
    assert extracted["external_evidence_url"] is None

    normalized = normalizer.normalize_record(extracted)
    assert normalized["external_evidence_available"] is False
    assert normalized["external_evidence_url"] is None


def test_fake_or_invented_provenance_rejected():
    gate = ValidationGate()
    record = {
        "name": "Fake Tool",
        "url": "https://faketool.com",
        "official_url": "https://faketool.com",
        "discovery_source_name": "GitHub API",
        "discovery_source_url": "ftp://malformed-endpoint",  # Malformed external URL
        "discovery_source_type": "API",
        "discovery_source_trust_level": "HIGH",
        "description": "This is a tool with malformed discovery provenance.",
        "description_grounded": True,
        "description_source_url": "https://faketool.com",
        "categories": ["Developer Tools"]
    }
    vr = VerificationResult(verification_status="ACCESSIBLE_VERIFIED", accessible=True)
    is_valid, reason = gate.validate(record, vr)
    assert is_valid is False
    assert "Malformed external discovery URL" in reason


def test_github_repo_url_preserved_and_homepage_separated():
    raw_repo_item = {
        "name": "vLLM",
        "url": "https://vllm.ai",
        "official_url": "https://vllm.ai",
        "company_name": "vllm-project",
        "company_url": "https://github.com/vllm-project",
        "description": "A high-throughput and memory-efficient LLM inference engine.",
        "category": "Developer Tools",
        "pricing_model": "Open Source",
        "github_stars": 30000,
        "github_repo_url": "https://github.com/vllm-project/vllm",
        "github_owner": "vllm-project",
        "discovery_source_name": "GitHub API",
        "discovery_source_url": "https://api.github.com/search/repositories",
        "discovery_source_type": "API",
        "discovery_source_trust_level": "HIGH",
        "external_evidence_available": True,
        "external_evidence_url": "https://github.com/vllm-project/vllm",
        "evidence_sources": [
            {
                "url": "https://github.com/vllm-project/vllm",
                "source_type": "GITHUB_REPOSITORY",
                "trust_level": "HIGH",
                "evidence_type": "CODE_REPOSITORY"
            }
        ]
    }

    extractor = ToolExtractor()
    extracted = extractor.extract(raw_repo_item, "GitHub API")
    normalizer = ToolNormalizer()
    normalized = normalizer.normalize_record(extracted)

    assert normalized["official_url"] == "https://vllm.ai"
    assert normalized["github_repo_url"] == "https://github.com/vllm-project/vllm"
    assert normalized["external_evidence_url"] == "https://github.com/vllm-project/vllm"
    assert normalized["official_url"] != normalized["external_evidence_url"]


def test_grounded_description_references_evidence_url():
    gate = ValidationGate()
    record = {
        "name": "Cursor",
        "url": "https://cursor.com",
        "official_url": "https://cursor.com",
        "discovery_source_name": "Official AI Directory Seed",
        "discovery_source_url": "internal://seed_tools",
        "discovery_source_type": "CURATED_SEED",
        "discovery_source_trust_level": "MEDIUM",
        "description": "An AI-first code editor built on VS Code for developers.",
        "description_grounded": True,
        "description_source_url": "https://cursor.com",
        "categories": ["Coding"]
    }
    vr = VerificationResult(
        verification_status="ACCESSIBLE_VERIFIED",
        accessible=True,
        official_domain_match=True
    )
    is_valid, reason = gate.validate(record, vr)
    assert is_valid is True
    assert record["description_source_url"] == "https://cursor.com"


def test_ungrounded_description_rejected():
    gate = ValidationGate()
    record = {
        "name": "Cursor",
        "url": "https://cursor.com",
        "official_url": "https://cursor.com",
        "discovery_source_name": "Official AI Directory Seed",
        "discovery_source_url": "internal://seed_tools",
        "discovery_source_type": "CURATED_SEED",
        "discovery_source_trust_level": "MEDIUM",
        "description": "Fabricated model description without evidence backing.",
        "description_grounded": False,  # Ungrounded
        "description_source_url": None,
        "categories": ["Coding"]
    }
    vr = VerificationResult(
        verification_status="ACCESSIBLE_VERIFIED",
        accessible=True,
        official_domain_match=True
    )
    is_valid, reason = gate.validate(record, vr)
    assert is_valid is False
    assert "not grounded" in reason.lower()


def test_access_blocked_with_authoritative_evidence_passes():
    gate = ValidationGate()
    record = {
        "name": "Claude",
        "url": "https://claude.ai",
        "official_url": "https://claude.ai",
        "discovery_source_name": "Official AI Registry",
        "discovery_source_url": "https://registry.ai/claude",
        "discovery_source_type": "OFFICIAL_REGISTRY",
        "discovery_source_trust_level": "HIGH",
        "external_evidence_available": True,
        "external_evidence_url": "https://registry.ai/claude",
        "evidence_sources": [
            {
                "url": "https://registry.ai/claude",
                "source_type": "OFFICIAL_REGISTRY",
                "trust_level": "HIGH",
                "evidence_type": "REGISTRY_ENTRY"
            }
        ],
        "description": "Next-generation AI assistant built by Anthropic.",
        "description_grounded": True,
        "description_source_url": "https://registry.ai/claude",
        "categories": ["AI Assistants"]
    }
    vr = VerificationResult(
        verification_status="ACCESS_BLOCKED",
        http_status=403,
        accessible=False,
        official_domain_match=True,
        reason="HTTP 403"
    )
    is_valid, reason = gate.validate(record, vr)
    assert is_valid is True
    assert record["verification_status"] == "ACCESS_BLOCKED"


def test_access_blocked_with_medium_or_unknown_evidence_rejected():
    gate = ValidationGate()
    record = {
        "name": "ChatGPT",
        "url": "https://chatgpt.com",
        "official_url": "https://chatgpt.com",
        "discovery_source_name": "Official AI Directory Seed",
        "discovery_source_url": "internal://seed_tools",
        "discovery_source_type": "CURATED_SEED",
        "discovery_source_trust_level": "MEDIUM",
        "external_evidence_available": False,
        "external_evidence_url": None,
        "description": "Conversational AI assistant powered by OpenAI GPT-4o models.",
        "description_grounded": True,
        "description_source_url": "internal://seed_tools",
        "categories": ["AI Assistants"]
    }
    vr = VerificationResult(
        verification_status="ACCESS_BLOCKED",
        http_status=403,
        accessible=False,
        official_domain_match=True,
        reason="HTTP 403"
    )
    is_valid, reason = gate.validate(record, vr)
    assert is_valid is False
    assert "insufficient source trust" in reason.lower()


def test_logo_failure_does_not_invalidate_identity():
    gate = ValidationGate()
    record = {
        "name": "Cursor",
        "url": "https://cursor.com",
        "official_url": "https://cursor.com",
        "discovery_source_name": "Official AI Directory Seed",
        "discovery_source_url": "internal://seed_tools",
        "discovery_source_type": "CURATED_SEED",
        "discovery_source_trust_level": "MEDIUM",
        "logo_verified": False,  # Logo not found or failed
        "logo_found": False,
        "description": "An AI-first code editor built on VS Code for developers.",
        "description_grounded": True,
        "description_source_url": "https://cursor.com",
        "categories": ["Coding"]
    }
    vr = VerificationResult(
        verification_status="ACCESSIBLE_VERIFIED",
        accessible=True,
        official_domain_match=True
    )
    is_valid, reason = gate.validate(record, vr)
    assert is_valid is True
    assert reason is None
    # Quality score is calculated even without logo
    assert record["quality_score"] > 0
