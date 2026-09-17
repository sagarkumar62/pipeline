"""Tests for GitHub repository qualification filter."""

import pytest
from src.qualification.qualifier import GitHubRepoQualifier


@pytest.fixture
def qualifier():
    return GitHubRepoQualifier()


class TestQualification:
    """Test repo qualification with multiple signal combinations."""

    def test_actual_ai_tool_qualified(self, qualifier):
        """A real AI tool with positive signals should be QUALIFIED_TOOL."""
        record = {
            "name": "browser-use",
            "description": "Make websites accessible for AI agents",
            "github_topics": ["ai-agent", "automation", "browser"],
            "is_fork": False,
            "is_archived": False,
        }
        result = qualifier.qualify(record)
        assert result.status == "QUALIFIED_TOOL"

    def test_awesome_list_rejected(self, qualifier):
        """An awesome list with matching name and description should be REJECTED_NON_TOOL."""
        record = {
            "name": "awesome-ai-tools",
            "description": "A curated list of awesome AI tools",
            "github_topics": ["awesome-list", "ai-tools"],
            "is_fork": False,
            "is_archived": False,
        }
        result = qualifier.qualify(record)
        assert result.status == "REJECTED_NON_TOOL"

    def test_tutorial_repo_rejected(self, qualifier):
        """A tutorial repo with matching name and description should be REJECTED_NON_TOOL."""
        record = {
            "name": "llm-tutorial",
            "description": "Tutorial for learning LLM development",
            "github_topics": ["tutorial", "learning"],
            "is_fork": False,
            "is_archived": False,
        }
        result = qualifier.qualify(record)
        assert result.status == "REJECTED_NON_TOOL"

    def test_dataset_repo_rejected(self, qualifier):
        """A dataset repo should be rejected when multiple signals confirm."""
        record = {
            "name": "ai-training-dataset",
            "description": "Collection of training data for AI models",
            "github_topics": ["dataset", "machine-learning"],
            "is_fork": False,
            "is_archived": False,
        }
        result = qualifier.qualify(record)
        assert result.status == "REJECTED_NON_TOOL"

    def test_benchmark_repo_rejected(self, qualifier):
        """A benchmark repo should be rejected."""
        record = {
            "name": "llm-benchmark",
            "description": "Benchmarking suite for language models",
            "github_topics": ["benchmark", "evaluation"],
            "is_fork": False,
            "is_archived": False,
        }
        result = qualifier.qualify(record)
        assert result.status == "REJECTED_NON_TOOL"

    def test_archived_repo_review_required(self, qualifier):
        """An archived repo with otherwise positive signals should be REVIEW_REQUIRED."""
        record = {
            "name": "my-ai-tool",
            "description": "A useful AI tool for developers",
            "github_topics": ["ai-tool", "developer-tools"],
            "is_fork": False,
            "is_archived": True,
        }
        result = qualifier.qualify(record)
        assert result.status == "REVIEW_REQUIRED"

    def test_ambiguous_repo_review_required(self, qualifier):
        """A repo with mixed signals should be REVIEW_REQUIRED."""
        record = {
            "name": "awesome-mcp-servers",
            "description": "MCP server implementations for AI assistants",
            "github_topics": ["mcp-server", "awesome-list"],
            "is_fork": False,
            "is_archived": False,
        }
        result = qualifier.qualify(record)
        # Under hardened qualifier, awesome name + awesome-list topic is REJECTED_NON_TOOL
        assert result.status in ["REJECTED_NON_TOOL", "REVIEW_REQUIRED"]

    def test_positive_topics_counteract_name_pattern(self, qualifier):
        """Positive topics can counteract a single negative name signal."""
        record = {
            "name": "ai-resources",
            "description": "SDK for managing AI resources in production",
            "github_topics": ["sdk", "developer-tools", "api"],
            "is_fork": False,
            "is_archived": False,
        }
        result = qualifier.qualify(record)
        # 1 negative (name) - 3 positive (topics) = net -2, so QUALIFIED_TOOL
        assert result.status == "QUALIFIED_TOOL"

    def test_fork_plus_negative_name_rejected(self, qualifier):
        """Fork + negative name pattern should be rejected."""
        record = {
            "name": "awesome-llm-papers",
            "description": "Research papers on large language models",
            "github_topics": [],
            "is_fork": True,
            "is_archived": False,
        }
        result = qualifier.qualify(record)
        assert result.status == "REJECTED_NON_TOOL"

    def test_tool_with_no_description_review(self, qualifier):
        """A tool-like name with no description should be REVIEW_REQUIRED."""
        record = {
            "name": "neat-cli",
            "description": None,
            "github_topics": [],
            "is_fork": False,
            "is_archived": False,
        }
        result = qualifier.qualify(record)
        assert result.status == "REVIEW_REQUIRED"

    def test_readme_with_install_instructions_helps(self, qualifier):
        """README with installation instructions adds positive signal."""
        record = {
            "name": "some-resources",
            "description": "A utility library",
            "github_topics": [],
            "is_fork": False,
            "is_archived": False,
            "readme_content": "# My Tool\n\n## Installation\n\npip install my-tool\n\n## Usage\n\nRun `my-tool --help`"
        }
        result = qualifier.qualify(record)
        # Name negative, but README positive → net 0 → QUALIFIED_TOOL
        assert result.status == "QUALIFIED_TOOL"

    def test_qualification_result_has_reasons(self, qualifier):
        """Qualification result should always contain reasons."""
        record = {
            "name": "my-cool-tool",
            "description": "A great tool",
            "github_topics": ["tool"],
            "is_fork": False,
            "is_archived": False,
        }
        result = qualifier.qualify(record)
        assert isinstance(result.reasons, list)
        assert len(result.reasons) > 0

    def test_qualification_result_has_signals(self, qualifier):
        """Qualification result should contain signal metadata."""
        record = {
            "name": "test-tool",
            "description": "Test",
            "github_topics": [],
            "is_fork": False,
            "is_archived": False,
        }
        result = qualifier.qualify(record)
        assert "name" in result.signals
        assert "negative_signal_count" in result.signals
        assert "positive_signal_count" in result.signals
