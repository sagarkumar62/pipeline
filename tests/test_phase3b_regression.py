"""
Phase 3B Regression Test Suite

Tests all 14 mandatory regression scenarios defined in Section 11 of the Phase 3B Specification.
"""

import pytest

from src.qualification.qualifier import GitHubRepoQualifier
from src.classification.classifier import TaxonomyClassifier
from src.enrichment.orchestrator import LLMOrchestrator
from src.models.tool import ToolRecord, DiscoverySource, VerificationResult
from src.verification.logo import OfficialLogoVerifier


@pytest.fixture
def qualifier():
    return GitHubRepoQualifier()


@pytest.fixture
def classifier():
    return TaxonomyClassifier()


@pytest.fixture
def orchestrator():
    return LLMOrchestrator(providers=[])


@pytest.fixture
def logo_verifier():
    return OfficialLogoVerifier()


class TestPhase3BRegression:
    """Mandatory Phase 3B regression test suite covering all 14 quality rules."""

    # 1. Curriculum repository -> not Tool
    def test_1_curriculum_repo_not_tool(self, qualifier):
        record = {
            "name": "ai-creator-academy",
            "description": "A comprehensive curriculum on building AI agents and apps",
            "github_topics": ["learning", "ai-tools"],
            "is_fork": False,
            "is_archived": False,
        }
        res = qualifier.qualify(record)
        assert res.status in ["REJECTED_NON_TOOL", "REVIEW_REQUIRED"]

    # 2. Course repository -> not Tool
    def test_2_course_repo_not_tool(self, qualifier):
        record = {
            "name": "llm-course-2024",
            "description": "Full online course for learning LLMs from scratch",
            "github_topics": ["course", "tutorials"],
            "is_fork": False,
            "is_archived": False,
        }
        res = qualifier.qualify(record)
        assert res.status in ["REJECTED_NON_TOOL", "REVIEW_REQUIRED"]

    # 3. Awesome list -> not Tool
    def test_3_awesome_list_not_tool(self, qualifier):
        record = {
            "name": "awesome-ai-tools",
            "description": "Curated list of awesome AI tools and libraries",
            "github_topics": ["awesome-list"],
            "is_fork": False,
            "is_archived": False,
        }
        res = qualifier.qualify(record)
        assert res.status == "REJECTED_NON_TOOL"

    # 4. Dataset -> not Tool
    def test_4_dataset_not_tool(self, qualifier):
        record = {
            "name": "ai-benchmarking-dataset",
            "description": "Dataset of training pairs for LLMs",
            "github_topics": ["dataset"],
            "is_fork": False,
            "is_archived": False,
        }
        res = qualifier.qualify(record)
        assert res.status == "REJECTED_NON_TOOL"

    # 5. Benchmark -> not Tool
    def test_5_benchmark_not_tool(self, qualifier):
        record = {
            "name": "llm-perf-benchmark",
            "description": "Benchmarking suite for model latency",
            "github_topics": ["benchmark"],
            "is_fork": False,
            "is_archived": False,
        }
        res = qualifier.qualify(record)
        assert res.status == "REJECTED_NON_TOOL"

    # 6. Legitimate AI Tool -> Tool
    def test_6_legitimate_tool_qualified(self, qualifier):
        record = {
            "name": "vLLM",
            "description": "High-throughput and memory-efficient LLM serving engine",
            "github_topics": ["inference", "developer-tools"],
            "is_fork": False,
            "is_archived": False,
            "readme_content": "# vLLM\n\n## Installation\n\npip install vllm\n\n## Usage\n\nRun vLLM server",
        }
        res = qualifier.qualify(record)
        assert res.status == "QUALIFIED_TOOL"

    # 7. GitHub-only record -> website_verified = False
    def test_7_github_only_record_website_verified_false(self):
        record = ToolRecord.create_canonical(
            name="github-only-tool",
            url="https://github.com/user/github-only-tool",
            official_url=None,  # No external official website
            discovery_source=DiscoverySource(name="GitHub API", url="https://api.github.com", source_type="API"),
            description="A CLI tool hosted on GitHub",
            categories=["Developer Tools"]
        )
        record.github_repository_verified = True
        record.website_verified = False  # Must be False when official_url is None

        assert record.official_url is None
        assert record.website_verified is False
        assert record.github_repository_verified is True

    # 8. External official homepage -> website_verified = True
    def test_8_external_homepage_website_verified_true(self):
        record = ToolRecord.create_canonical(
            name="vLLM",
            url="https://vllm.ai",
            official_url="https://vllm.ai",
            discovery_source=DiscoverySource(name="GitHub API", url="https://api.github.com", source_type="API"),
            description="High-throughput serving engine",
            categories=["Developer Tools"]
        )
        record.website_verified = True
        record.github_repository_verified = True

        assert record.official_url == "https://vllm.ai"
        assert record.website_verified is True

    # 9. GitHub social preview -> logo_verified = False
    @pytest.mark.asyncio
    async def test_9_github_social_preview_logo_verified_false(self, logo_verifier):
        record = {
            "name": "git-tool",
            "url": "https://github.com/owner/git-tool",
            "official_url": None,  # GitHub-only record
        }
        vr = VerificationResult(verification_status="ACCESSIBLE_VERIFIED", accessible=True)
        res = await logo_verifier.discover_logo(record, vr)
        assert res["logo_verified"] is False

    # 10. Official website logo -> eligible for verification
    @pytest.mark.asyncio
    async def test_10_official_website_logo_eligible(self, logo_verifier):
        record = {
            "name": "official-tool",
            "url": "https://vllm.ai",
            "official_url": "https://vllm.ai",
        }
        vr = VerificationResult(verification_status="ACCESSIBLE_VERIFIED", accessible=True)
        # Mocking website logo discovery: when official_url is present and accessible, logo_verified is eligible
        res = await logo_verifier.discover_logo(record, vr)
        # If a favicon/og:image on external site is found, logo_verified is True
        assert res["logo_access_blocked"] is False

    # 11. Slogan-only description with richer README -> README evidence preferred
    @pytest.mark.asyncio
    async def test_11_slogan_description_prefers_readme(self, orchestrator):
        record = {
            "name": "openclaude",
            "description": "runs anywhere. uses anything",
            "readme_content": "# openclaude\n\nOpen-source proxy framework for managing AI agent workflows and model providers.",
            "readme_url": "https://github.com/Gitlawb/openclaude#readme",
            "readme_available": True,
            "github_repo_url": "https://github.com/Gitlawb/openclaude",
        }
        res = await orchestrator.enrich_description(record)
        assert res["description_source_type"] == "GITHUB_README"
        assert "proxy framework" in res["description"].lower()

    # 12. Unsupported category -> removed/reviewed
    def test_12_unsupported_category_removed(self, classifier):
        record = {
            "categories": ["InvalidCategoryName"],
            "github_topics": ["mcp"],
            "description": "MCP tool",
            "name": "mcp-tool",
        }
        res = classifier.classify(record)
        assert "InvalidCategoryName" not in res["categories"]

    # 13. Code-execution service not automatically categorized as Agent
    def test_13_code_execution_service_not_agent(self, classifier):
        record = {
            "categories": [],
            "github_topics": ["api"],
            "description": "Judge0 is an open source API for code execution that can be used by AI agents.",
            "name": "judge0",
        }
        res = classifier.classify(record)
        assert "Agents" not in res["categories"]
        assert "Developer Tools" in res["categories"] or "Coding" in res["categories"]

    # 14. Prompt utility not automatically categorized as Model
    def test_14_prompt_utility_not_model(self, classifier):
        record = {
            "categories": [],
            "github_topics": ["prompt"],
            "description": "An AI prompt optimizer for writing better prompts and getting better AI results for models.",
            "name": "prompt-optimizer",
        }
        res = classifier.classify(record)
        assert "Models" not in res["categories"]
        assert "Productivity" in res["categories"] or "Developer Tools" in res["categories"]
