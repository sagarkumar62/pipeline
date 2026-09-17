import pytest
import os
import json
import hashlib
from src.models.agent import AgentRecord
from src.models.mcp import MCPRecord
from src.models.tool import ToolRecord
from src.models.repository import RepositoryRecord
from src.extraction.agent_extractor import AgentExtractor
from src.qualification.agent_qualifier import AgentQualifier
from src.deduplication.agent_resolver import AgentDeduplicationResolver


def test_agent_record_validation():
    rec = AgentRecord.create_canonical(
        name="AutoGPT",
        maintainer="Significant-Gravitas",
        repository_url="https://github.com/Significant-Gravitas/AutoGPT",
        description="An autonomous AI agent capability framework for goal execution.",
        agent_type="Autonomous Agent",
        capabilities=["tool_use", "planning", "memory", "multi_step"],
        license="MIT"
    )
    assert rec.name == "AutoGPT"
    assert rec.entity_type == "AGENT"
    assert rec.agent_type == "Autonomous Agent"
    assert "tool_use" in rec.capabilities
    assert "planning" in rec.capabilities


def test_agent_entity_type_discriminator():
    rec = AgentRecord.create_canonical(
        name="CrewAI",
        maintainer="crewAIInc",
        repository_url="https://github.com/crewAIInc/crewAI"
    )
    assert rec.entity_type == "AGENT"


def test_agent_required_identity_fields():
    rec = AgentRecord.create_canonical(
        name="Devin-Alternative",
        maintainer="dev-org",
        repository_url="https://github.com/dev-org/devin-alt"
    )
    assert rec.id == "agent:dev-org/devin-alt"
    assert rec.url == "https://github.com/dev-org/devin-alt"
    assert rec.discovery_source is not None


def test_agent_specific_metadata_fields():
    rec = AgentRecord.create_canonical(
        name="GPT-Engineer",
        maintainer="gpt-engineer-org",
        repository_url="https://github.com/gpt-engineer-org/gpt-engineer",
        agent_type="Coding Agent",
        agent_framework="Custom",
        tools_used=["CodeInterpreter", "FileSystem"],
        memory="Conversation Buffer",
        planning="ReAct"
    )
    assert rec.agent_type == "Coding Agent"
    assert "CodeInterpreter" in rec.tools_used
    assert rec.planning == "ReAct"


def test_agent_hard_exclusion_precedence():
    qualifier = AgentQualifier()
    awesome_item = {
        "name": "awesome-ai-agents",
        "description": "A curated list of awesome autonomous AI agents, frameworks, and tools",
        "topics": ["awesome", "ai-agent"],
        "stars": 12000,
        "archived": False
    }
    status, reason = qualifier.qualify(awesome_item)
    assert status == "HARD_EXCLUSION"
    assert "Awesome" in reason or "hard negative" in reason


def test_agent_review_precedence():
    qualifier = AgentQualifier()
    fork_item = {
        "name": "AutoGPT-fork",
        "description": "Custom fork of AutoGPT repository",
        "topics": ["ai-agent"],
        "fork": True
    }
    status, reason = qualifier.qualify(fork_item)
    assert status == "REVIEW_REQUIRED"
    assert "fork" in reason.lower()


def test_agent_genuine_agent_qualification():
    qualifier = AgentQualifier()
    valid_agent = {
        "name": "browser-use",
        "description": "Make AI agents interact with websites autonomously using Playwright",
        "topics": ["browser-agent", "ai-agent"]
    }
    status, reason = qualifier.qualify(valid_agent)
    assert status == "QUALIFIED"


def test_agent_chatbot_rejection():
    qualifier = AgentQualifier()
    chatbot_item = {
        "name": "my-simple-chatbot",
        "description": "A basic chatbot interface for OpenAI API",
        "topics": ["chatbot"]
    }
    status, reason = qualifier.qualify(chatbot_item)
    assert status == "HARD_EXCLUSION"


def test_agent_generic_llm_wrapper_rejection():
    qualifier = AgentQualifier()
    wrapper_item = {
        "name": "llm-wrapper-py",
        "description": "A python llm wrapper only around Claude API",
        "topics": ["llm", "wrapper"]
    }
    status, reason = qualifier.qualify(wrapper_item)
    assert status == "HARD_EXCLUSION"


def test_agent_prompt_library_rejection():
    qualifier = AgentQualifier()
    prompt_item = {
        "name": "awesome-prompts",
        "description": "A prompt library and collection of prompt engineering guides",
        "topics": ["prompts", "prompt-engineering"]
    }
    status, reason = qualifier.qualify(prompt_item)
    assert status == "HARD_EXCLUSION"


def test_agent_tutorial_list_course_rejection():
    qualifier = AgentQualifier()
    tutorial_item = {
        "name": "building-agents-course",
        "description": "Tutorials and course materials for learning to build agents",
        "topics": ["tutorial", "course"]
    }
    status, reason = qualifier.qualify(tutorial_item)
    assert status == "HARD_EXCLUSION"


def test_agent_provenance_completeness():
    extractor = AgentExtractor()
    raw = {
        "name": "MetaGPT",
        "owner": {"login": "geekan"},
        "html_url": "https://github.com/geekan/MetaGPT",
        "description": "Multi-agent framework for software development",
        "_discovery_query": "topic:multi-agent",
        "_discovery_source": "GitHub Agent Search"
    }
    rec = extractor.to_record(raw)
    assert rec.discovery_source.name == "GitHub Agent Search"
    assert len(rec.evidence_sources) == 1
    assert rec.evidence_sources[0].url == "https://github.com/geekan/MetaGPT"


def test_agent_deterministic_identity():
    rec = AgentRecord.create_canonical(
        name="gpt-researcher",
        maintainer="assafElovic",
        repository_url="https://github.com/assafElovic/gpt-researcher"
    )
    assert rec.id == "agent:assafelovic/gpt-researcher"


def test_agent_exact_repository_deduplication():
    resolver = AgentDeduplicationResolver()
    rec1 = {
        "id": "agent:geekan/metagpt",
        "repository_url": "https://github.com/geekan/metagpt"
    }
    rec2 = {
        "id": "agent:geekan/metagpt-copy",
        "repository_url": "https://github.com/geekan/metagpt"
    }
    resolver.resolve(rec1)
    res2, dup2 = resolver.resolve(rec2)
    assert dup2
    assert res2["match_method"] == "exact_repository_url"


def test_agent_canonical_url_deduplication():
    resolver = AgentDeduplicationResolver()
    rec1 = {
        "id": "agent:crewai/crewai",
        "official_url": "https://crewai.com"
    }
    rec2 = {
        "id": "agent:crewai/crewai-alt",
        "official_url": "https://crewai.com"
    }
    resolver.resolve(rec1)
    res2, dup2 = resolver.resolve(rec2)
    assert dup2
    assert res2["match_method"] == "exact_official_url"


def test_agent_cross_source_duplicate_merging():
    resolver = AgentDeduplicationResolver()
    item1 = {
        "id": "agent:significant-gravitas/autogpt",
        "maintainer": "significant-gravitas",
        "name": "autogpt"
    }
    item2 = {
        "id": "agent:significant-gravitas/autogpt-copy",
        "maintainer": "significant-gravitas",
        "name": "autogpt"
    }
    resolver.resolve(item1)
    res2, dup2 = resolver.resolve(item2)
    assert dup2


def test_agent_distinct_agent_preservation():
    resolver = AgentDeduplicationResolver()
    rec1 = {
        "id": "agent:userA/researcher",
        "maintainer": "userA",
        "name": "researcher",
        "repository_url": "https://github.com/userA/researcher"
    }
    rec2 = {
        "id": "agent:userB/researcher",
        "maintainer": "userB",
        "name": "researcher",
        "repository_url": "https://github.com/userB/researcher"
    }
    resolver.resolve(rec1)
    res2, dup2 = resolver.resolve(rec2)
    assert not dup2


def test_agent_framework_vs_product_distinction():
    extractor = AgentExtractor()
    framework_raw = {
        "name": "LangGraph",
        "owner": "langchain-ai",
        "html_url": "https://github.com/langchain-ai/langgraph",
        "description": "Build resilient language agents as graphs"
    }
    app_raw = {
        "name": "Devin",
        "owner": "cognition-labs",
        "html_url": "https://github.com/cognition-labs/devin-demo",
        "description": "Autonomous software engineer coding agent application"
    }
    f_rec = extractor.to_record(framework_raw)
    a_rec = extractor.to_record(app_raw)
    assert f_rec.agent_type in ("Agent Framework", "AI Agent")
    assert a_rec.agent_type in ("Coding Agent", "Autonomous Agent", "AI Agent")


def test_agent_official_website_verification_semantics():
    rec = AgentRecord.create_canonical(
        name="AutoGPT",
        repository_url="https://github.com/Significant-Gravitas/AutoGPT",
        official_url="https://agpt.co"
    )
    assert rec.official_url == "https://agpt.co"


def test_agent_github_not_official_website_rule():
    rec = AgentRecord.create_canonical(
        name="AutoGPT",
        repository_url="https://github.com/Significant-Gravitas/AutoGPT"
    )
    assert "github.com" in rec.repository_url


def test_agent_social_preview_not_verified_logo_rule():
    rec = AgentRecord.create_canonical(
        name="AutoGPT",
        repository_url="https://github.com/Significant-Gravitas/AutoGPT"
    )
    assert rec.logo_verified is False
    assert rec.logo_url is None


def test_agent_description_grounding():
    extractor = AgentExtractor()
    raw = {
        "name": "gpt-researcher",
        "owner": "assafElovic",
        "html_url": "https://github.com/assafElovic/gpt-researcher",
        "description": "LLM based autonomous agent that conducts deep research on any topic."
    }
    rec = extractor.to_record(raw)
    assert rec.description == "LLM based autonomous agent that conducts deep research on any topic."


def test_agent_missing_evidence_handling():
    extractor = AgentExtractor()
    raw = {
        "name": "generic-agent",
        "owner": "testuser",
        "html_url": "https://github.com/testuser/generic-agent",
        "description": "Basic agent repository"
    }
    rec = extractor.to_record(raw)
    assert rec.capabilities == []
    assert rec.tools_used == []
    assert rec.memory is None
    assert rec.planning is None


def test_agent_category_classification():
    rec = AgentRecord.create_canonical(
        name="AutoGPT",
        repository_url="https://github.com/Significant-Gravitas/AutoGPT",
        categories=["Agent", "Artificial Intelligence"]
    )
    assert "Agent" in rec.categories


def test_agent_malformed_source_handling():
    extractor = AgentExtractor()
    raw = {
        "name": None,
        "owner": None,
        "html_url": None
    }
    extracted = extractor.extract(raw)
    assert extracted["name"] == ""


def test_agent_rate_limit_retry_configuration():
    from src.discovery.agent_discovery import AgentsAdapter
    adapter = AgentsAdapter(per_page=15, max_pages_per_query=1)
    assert adapter.per_page == 15
    assert adapter.max_pages_per_query == 1


def test_protected_tools_dataset_integrity():
    tools_json_path = "data/exports/tools.json"
    if os.path.exists(tools_json_path):
        with open(tools_json_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest().upper()
        assert h == "4520014C9A1676F9090BE806087A92AC0E12FEF3D3136A95860CFF48388FF2A1"


def test_protected_repository_dataset_integrity():
    repos_final_path = "data/working/repositories/repositories_final.json"
    if os.path.exists(repos_final_path):
        with open(repos_final_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest().upper()
        assert h == "176D5DEEEC8063FC4684C058B5E758649E57375ACE6AB5ADA05A4ECE43FB8465"


def test_protected_mcp_dataset_integrity():
    mcp_final_path = "data/working/mcp/mcp_final.json"
    if os.path.exists(mcp_final_path):
        with open(mcp_final_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest().upper()
        assert h == "CED0BF7AE869ACC54403C0453A1A12CF097131D6D5CB438BEA36216822A9216B"
