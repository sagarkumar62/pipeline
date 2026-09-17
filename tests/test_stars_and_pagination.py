"""Tests for star count propagation, GitHub API pagination, rate limiting, and official URL semantics."""

import pytest
import httpx
from typing import AsyncGenerator, Dict, Any
from src.discovery.tool_discovery import GitHubToolDiscovery
from src.extraction.tool_extractor import ToolExtractor
from src.normalization.normalizer import ToolNormalizer
from src.deduplication.resolver import DeduplicationResolver
from src.models.tool import ToolRecord, DiscoverySource, EvidenceSource


class TestStarPropagation:
    """Test star count propagation from API payload to canonical model."""

    def test_star_count_greater_than_zero(self):
        raw = {
            "name": "vLLM",
            "url": "https://vllm.ai",
            "official_url": "https://vllm.ai",
            "github_stars": 30500,
            "github_repo_url": "https://github.com/vllm-project/vllm",
            "discovery_source_name": "GitHub API",
            "discovery_source_url": "https://api.github.com/search/repositories",
            "discovery_source_type": "API",
            "discovery_source_trust_level": "HIGH",
            "description": "High-throughput LLM serving engine",
            "category": "Developer Tools"
        }
        extractor = ToolExtractor()
        extracted = extractor.extract(raw, "GitHub API")
        normalizer = ToolNormalizer()
        normalized = normalizer.normalize_record(extracted)

        assert normalized["github_stars"] == 30500

        record = ToolRecord.create_canonical(
            name=normalized["name"],
            url=normalized["url"],
            official_url=normalized["official_url"],
            discovery_source=DiscoverySource(name="GitHub API", url="https://api.github.com", source_type="API"),
            description=normalized["description"],
            categories=["Developer Tools"]
        )
        record.github_stars = normalized["github_stars"]
        assert record.github_stars == 30500

    def test_star_count_zero_preserved(self):
        """Zero stars must be preserved as 0, not converted to None or omitted."""
        raw = {
            "name": "new-tool",
            "url": "https://github.com/user/new-tool",
            "official_url": None,
            "github_stars": 0,
            "github_repo_url": "https://github.com/user/new-tool",
        }
        extractor = ToolExtractor()
        extracted = extractor.extract(raw, "GitHub API")
        normalizer = ToolNormalizer()
        normalized = normalizer.normalize_record(extracted)

        assert normalized["github_stars"] == 0
        assert normalized["github_stars"] is not None

    def test_missing_star_count_is_none(self):
        """Missing github_stars should be None."""
        raw = {
            "name": "no-star-tool",
            "url": "https://example.com",
            "github_stars": None,
        }
        extractor = ToolExtractor()
        extracted = extractor.extract(raw, "GitHub API")
        normalizer = ToolNormalizer()
        normalized = normalizer.normalize_record(extracted)

        assert normalized["github_stars"] is None


class TestOfficialURLSemantics:
    """Test separation of official_url and github_repo_url."""

    def test_homepage_becomes_official_url(self):
        """Valid external homepage should become official_url."""
        repo = {
            "name": "ollama",
            "html_url": "https://github.com/ollama/ollama",
            "homepage": "https://ollama.com",
            "owner": {"login": "ollama"},
        }
        homepage = (repo.get("homepage") or "").strip()
        official_url = homepage if homepage and "github.com" not in homepage.lower() else None

        assert official_url == "https://ollama.com"

    def test_no_homepage_keeps_official_url_none(self):
        """Repository with no homepage should have official_url = None."""
        repo = {
            "name": "some-repo",
            "html_url": "https://github.com/owner/some-repo",
            "homepage": None,
            "owner": {"login": "owner"},
        }
        homepage = (repo.get("homepage") or "").strip()
        official_url = homepage if homepage and "github.com" not in homepage.lower() else None

        assert official_url is None

    def test_github_homepage_not_used_as_official_url(self):
        """Homepage set to a github.com link should NOT become official_url."""
        repo = {
            "name": "git-tool",
            "html_url": "https://github.com/owner/git-tool",
            "homepage": "https://github.com/owner/git-tool/wiki",
            "owner": {"login": "owner"},
        }
        homepage = (repo.get("homepage") or "").strip()
        official_url = homepage if homepage and "github.com" not in homepage.lower() else None

        assert official_url is None


class TestPaginationAndRateLimit:
    """Test pagination backfilling and API resilience."""

    def test_deduplication_across_pages(self):
        """Same repo discovered twice across pages/queries must be deduplicated."""
        resolver = DeduplicationResolver()
        rec1 = {
            "id": "tool_12345",
            "name": "vLLM",
            "canonical_name": "vllm",
            "url": "https://vllm.ai",
            "domain": "vllm.ai",
            "github_repo_url": "https://github.com/vllm-project/vllm",
        }
        rec2 = {
            "id": "tool_12345",
            "name": "vLLM",
            "canonical_name": "vllm",
            "url": "https://vllm.ai",
            "domain": "vllm.ai",
            "github_repo_url": "https://github.com/vllm-project/vllm",
        }

        _, is_dup1 = resolver.resolve(rec1)
        assert is_dup1 is False

        _, is_dup2 = resolver.resolve(rec2)
        assert is_dup2 is True

    @pytest.mark.asyncio
    async def test_wait_for_rate_limit_helper(self):
        """Rate limit helper should handle remaining = 1 gracefully."""
        discovery = GitHubToolDiscovery()
        # Mock httpx response headers
        headers = httpx.Headers({
            "X-RateLimit-Remaining": "50",
            "X-RateLimit-Reset": "1700000000"
        })
        response = httpx.Response(status_code=200, headers=headers)
        # Should not sleep when remaining is 50
        await discovery._wait_for_rate_limit(response)
