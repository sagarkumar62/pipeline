"""
Unit tests for hardened GitHubRepoQualifier (Phase 6B Remediation).
"""

import pytest
from src.qualification.qualifier import GitHubRepoQualifier, QualificationResult


@pytest.fixture
def qualifier():
    return GitHubRepoQualifier()


def test_reject_hard_non_tools(qualifier):
    reject_cases = [
        ("awesome-ai-tools", "Finding the AI tools you need!", ["ai-tools"]),
        ("awesome-claude-code-subagents", "Collection of subagents", ["awesome"]),
        ("awesome-mcp-servers-zh", "Awesome MCP servers", ["awesome-list"]),
        ("pentest-reports", "Collection of penetration test reports", ["security"]),
        ("agent-course-materials", "Course materials for AI agents", ["course"]),
        ("ai-agent-tutorials", "Tutorials for building AI agents", ["tutorial"]),
        ("llm-interview-questions", "Interview questions for LLMs", ["interview"]),
        ("MakeMoneyWithAI", "A list of open-source AI projects", ["mcp", "ai-agent"]),
    ]

    for name, desc, topics in reject_cases:
        res = qualifier.qualify({"name": name, "description": desc, "github_topics": topics})
        assert res.status == "REJECTED_NON_TOOL", f"Expected {name} to be REJECTED_NON_TOOL, got {res.status}"


def test_review_boundary_cases(qualifier):
    review_cases = [
        ("curated-mcp-list", "A list of MCP servers", ["mcp"]),
        ("awesome-templates-repo", "Templates for tools", ["mcp", "templates"]),
        ("agent-research-papers", "Papers about AI agents", ["ai-agents", "papers"]),
        ("langchain-experiments", "Experiments with LangChain", ["ai-agents"]),
    ]

    for name, desc, topics in review_cases:
        res = qualifier.qualify({"name": name, "description": desc, "github_topics": topics})
        assert res.status == "REVIEW_REQUIRED", f"Expected {name} to be REVIEW_REQUIRED, got {res.status}"


def test_qualify_legitimate_tools(qualifier):
    qualify_cases = [
        ("aihub", "All-in-one Kotlin app for AI", ["ai-tools", "mobile"]),
        ("funzzy", "Lightweight watcher CLI tool", ["cli", "rust"]),
        ("vomit", "Clean up Claude token vomit", ["claude-code"]),
        ("WorkWit", "Self-hosted enterprise AI agent platform", ["ai-agents"]),
        ("Calyx", "Native macOS terminal app for coding agents", ["terminal"]),
        ("kubeterm", "Kubernetes AI terminal UI", ["k8s"]),
    ]

    for name, desc, topics in qualify_cases:
        res = qualifier.qualify({"name": name, "description": desc, "github_topics": topics})
        assert res.status == "QUALIFIED_TOOL", f"Expected {name} to be QUALIFIED_TOOL, got {res.status}"
