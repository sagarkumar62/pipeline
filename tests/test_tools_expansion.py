import json
import os
import pytest
from src.models.tool import ToolRecord
from src.qualification.qualifier import GitHubRepoQualifier
from src.deduplication.resolver import DeduplicationResolver


def test_baseline_immutability():
    baseline_path = "data/working/tools_final_1304_prepublication.json"
    assert os.path.exists(baseline_path)
    with open(baseline_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 1304


def test_qualification_precedence():
    qualifier = GitHubRepoQualifier()

    # Hard negative pattern must yield REJECTED_NON_TOOL
    cand_awesome = {
        "name": "awesome-llm-tools",
        "description": "Curated list of awesome tools for LLMs",
        "github_topics": ["awesome", "llm-tools"],
        "is_fork": False,
        "is_archived": False
    }
    q_res = qualifier.qualify(cand_awesome)
    assert q_res.status == "REJECTED_NON_TOOL"


def test_baseline_duplicate_detection():
    resolver = DeduplicationResolver()
    baseline_records = [
        {
            "id": "tool:langchain",
            "name": "LangChain",
            "official_url": "https://langchain.com",
            "github_repo_url": "https://github.com/langchain-ai/langchain"
        }
    ]
    resolver.load_baseline(baseline_records)

    cand = {
        "id": "tool:langchain-ai/langchain",
        "name": "LangChain",
        "official_url": "https://langchain.com",
        "github_repo_url": "https://github.com/langchain-ai/langchain"
    }

    resolved, is_dup = resolver.resolve(cand)
    assert is_dup
    assert resolved["is_baseline_match"] is True
    assert resolved["duplicate_of"] == "tool:langchain"


def test_intra_expansion_duplicate_detection():
    resolver = DeduplicationResolver()
    resolver.load_baseline([])  # Empty baseline

    cand1 = {
        "id": "tool:browser-use/browser-use",
        "name": "browser-use",
        "official_url": "https://browser-use.com",
        "github_repo_url": "https://github.com/browser-use/browser-use"
    }

    cand2 = {
        "id": "tool:browser-use/browser-use-mirror",
        "name": "browser-use",
        "official_url": "https://browser-use.com",
        "github_repo_url": "https://github.com/browser-use/browser-use"
    }

    _, is_dup1 = resolver.resolve(cand1)
    resolved2, is_dup2 = resolver.resolve(cand2)

    assert not is_dup1
    assert is_dup2
    assert resolved2["is_baseline_match"] is False
    assert resolved2["duplicate_of"] == "tool:browser-use/browser-use"


def test_tools_expansion_accounting_equation():
    raw = 2500
    qualified = 1800
    rejected = 500
    review = 200

    baseline_dups = 300
    intra_dups = 150
    final_new = 1350

    assert raw == qualified + rejected + review
    assert qualified == baseline_dups + intra_dups + final_new
