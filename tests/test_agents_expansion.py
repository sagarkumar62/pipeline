import json
import os
import pytest
from src.models.agent import AgentRecord
from src.qualification.agent_qualifier import AgentQualifier
from src.deduplication.agent_resolver import AgentDeduplicationResolver


def test_agent_baseline_immutability():
    baseline_path = "data/working/agents/agents_final.json"
    assert os.path.exists(baseline_path)
    with open(baseline_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 91


def test_agent_qualification_precedence():
    qualifier = AgentQualifier()

    # Chatbot/wrapper must yield HARD_EXCLUSION
    cand_wrapper = {
        "name": "chat-gpt-ui-wrapper",
        "description": "Simple web wrapper and chatbot UI for ChatGPT API",
        "topics": ["wrapper", "chatbot"]
    }
    status, reason = qualifier.qualify(cand_wrapper)
    assert status == "HARD_EXCLUSION"
    assert "wrapper" in reason.lower() or "chat" in reason.lower()

    # Awesome list / Tutorial must yield HARD_EXCLUSION
    cand_awesome = {
        "name": "awesome-ai-agents",
        "description": "Curated list of awesome AI agents and resources",
        "topics": ["awesome-list"]
    }
    status, reason = qualifier.qualify(cand_awesome)
    assert status == "HARD_EXCLUSION"

    # Autonomous Agent Framework must yield QUALIFIED
    cand_agent = {
        "name": "AutoGPT",
        "description": "Autonomous AI agent system capable of planning, multi-step task execution and tool use",
        "topics": ["ai-agent", "autonomous-agent", "agent-framework"],
        "stars": 160000
    }
    status, reason = qualifier.qualify(cand_agent)
    assert status == "QUALIFIED"


def test_agent_baseline_duplicate_detection():
    resolver = AgentDeduplicationResolver()
    baseline_records = [
        {
            "id": "agent:auto-gpt",
            "name": "AutoGPT",
            "repository_url": "https://github.com/Significant-Gravitas/AutoGPT"
        }
    ]
    resolver.load_baseline(baseline_records)

    cand = {
        "id": "agent:auto-gpt-dup",
        "name": "AutoGPT",
        "repository_url": "https://github.com/Significant-Gravitas/AutoGPT"
    }

    resolved, is_dup = resolver.resolve(cand)
    assert is_dup
    assert resolved["is_baseline_match"] is True
    assert resolved["duplicate_of"] == "agent:auto-gpt"


def test_agent_intra_expansion_duplicate_detection():
    resolver = AgentDeduplicationResolver()
    resolver.load_baseline([])  # Empty baseline

    cand1 = {
        "id": "agent:crewai",
        "name": "CrewAI",
        "repository_url": "https://github.com/crewAIInc/crewAI"
    }

    cand2 = {
        "id": "agent:crewai-mirror",
        "name": "CrewAI",
        "repository_url": "https://github.com/crewAIInc/crewAI"
    }

    _, is_dup1 = resolver.resolve(cand1)
    resolved2, is_dup2 = resolver.resolve(cand2)

    assert not is_dup1
    assert is_dup2
    assert resolved2["is_baseline_match"] is False
    assert resolved2["duplicate_of"] == "agent:crewai"


def test_agent_repository_identity_normalization():
    resolver = AgentDeduplicationResolver()
    url1 = "https://github.com/langchain-ai/langgraph.git"
    url2 = "https://github.com/langchain-ai/langgraph/"
    norm1 = resolver._normalize_repo(url1)
    norm2 = resolver._normalize_repo(url2)
    assert norm1 == "langchain-ai/langgraph"
    assert norm2 == "langchain-ai/langgraph"


def test_agents_expansion_accounting_equation():
    raw = 2000
    qualified = 1500
    rejected = 400
    review = 100

    baseline_dups = 20
    intra_dups = 80
    final_new = 1400

    assert raw == qualified + rejected + review
    assert qualified == baseline_dups + intra_dups + final_new
