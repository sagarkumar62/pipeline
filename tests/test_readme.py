"""Tests for README extraction and description grounding."""

import pytest
from src.enrichment.orchestrator import LLMOrchestrator


@pytest.fixture
def orchestrator():
    return LLMOrchestrator(providers=[])  # No LLM providers for deterministic tests


class TestREADMEExtraction:
    """Tests for README-based description grounding."""

    @pytest.mark.asyncio
    async def test_valid_readme_used_when_no_description(self, orchestrator):
        """When no description exists, README should be used."""
        record = {
            "name": "my-tool",
            "description": None,
            "readme_content": "# My Tool\n\nA powerful command-line tool for processing AI data pipelines efficiently.\n\n## Installation\npip install my-tool",
            "readme_url": "https://github.com/user/my-tool#readme",
            "readme_available": True,
            "github_repo_url": "https://github.com/user/my-tool",
        }
        result = await orchestrator.enrich_description(record)
        assert result["description"] is not None
        assert result["description_grounded"] is True
        assert result["description_source_type"] == "GITHUB_README"
        assert result["description_generation_method"] == "EXTRACTED_FROM_README"

    @pytest.mark.asyncio
    async def test_missing_readme_graceful_fallback(self, orchestrator):
        """When README is missing and no description, description should be None."""
        record = {
            "name": "no-readme-tool",
            "description": None,
            "readme_content": None,
            "readme_url": None,
            "readme_available": False,
        }
        result = await orchestrator.enrich_description(record)
        assert result["description"] is None
        assert result["description_grounded"] is False
        assert result["description_generation_method"] == "NONE"

    @pytest.mark.asyncio
    async def test_malformed_readme_handled(self, orchestrator):
        """Malformed README (very short/empty) should not produce a description."""
        record = {
            "name": "bad-readme",
            "description": None,
            "readme_content": "# Title\n\n\n",
            "readme_url": "https://github.com/user/bad-readme#readme",
            "readme_available": True,
        }
        result = await orchestrator.enrich_description(record)
        # Too short to extract meaningful paragraph
        assert result["description_grounded"] is False or result["description"] is None

    @pytest.mark.asyncio
    async def test_oversized_readme_truncated(self, orchestrator):
        """Large README should be handled without errors."""
        long_content = "# Tool\n\nThis is a great tool for processing data.\n\n" + ("x" * 10000)
        record = {
            "name": "big-readme",
            "description": None,
            "readme_content": long_content,
            "readme_url": "https://github.com/user/big-readme#readme",
            "readme_available": True,
            "github_repo_url": "https://github.com/user/big-readme",
        }
        result = await orchestrator.enrich_description(record)
        # Should still work — extracts first paragraph
        assert result["description"] is not None
        assert result["description_grounded"] is True

    @pytest.mark.asyncio
    async def test_description_preferred_over_readme(self, orchestrator):
        """Repository description should be preferred over README."""
        record = {
            "name": "dual-source",
            "description": "A fast vector database for AI applications",
            "readme_content": "# Dual Source\n\nThis tool does many things.\n\n## Installation",
            "readme_url": "https://github.com/user/dual-source#readme",
            "readme_available": True,
            "github_repo_url": "https://github.com/user/dual-source",
        }
        result = await orchestrator.enrich_description(record)
        assert result["description"] == "A fast vector database for AI applications"
        assert result["description_source_type"] == "GITHUB_REPOSITORY_DESCRIPTION"

    @pytest.mark.asyncio
    async def test_description_only_repo(self, orchestrator):
        """Repo with only description (no README) should use description."""
        record = {
            "name": "desc-only",
            "description": "Simple CLI tool for text analysis",
            "readme_content": None,
            "readme_available": False,
            "github_repo_url": "https://github.com/user/desc-only",
        }
        result = await orchestrator.enrich_description(record)
        assert result["description_grounded"] is True
        assert result["description_source_type"] == "GITHUB_REPOSITORY_DESCRIPTION"

    @pytest.mark.asyncio
    async def test_readme_badges_skipped(self, orchestrator):
        """README with only badges/images should not produce a description."""
        record = {
            "name": "badge-only",
            "description": None,
            "readme_content": "# Badge Only\n\n![Build](https://img.shields.io/badge/build-passing)\n[![Coverage](https://codecov.io/badge)]\n\n",
            "readme_url": "https://github.com/user/badge-only#readme",
            "readme_available": True,
        }
        result = await orchestrator.enrich_description(record)
        # No meaningful paragraph after badges
        assert result["description_grounded"] is False or result["description"] is None
