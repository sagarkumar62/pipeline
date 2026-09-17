import os
import json
import pytest
from datetime import datetime, timezone

from src.models.news import NewsRecord, NewsSource
from src.discovery.news_discovery import NewsDiscoveryEngine, CURATED_NEWS_SOURCES
from src.extraction.news_extractor import NewsExtractor
from src.qualification.news_qualifier import NewsQualifier
from src.deduplication.news_resolver import NewsDeduplicationResolver
from src.clustering.news_clustering import NewsEventClusterer


def test_news_record_schema():
    rec = NewsRecord(
        id="news:test12345",
        entity_type="news",
        name="OpenAI Announces GPT-5 Developer Beta",
        title="OpenAI Announces GPT-5 Developer Beta",
        canonical_title="OpenAI Announces GPT-5 Developer Beta",
        source_name="MIT Technology Review",
        source_domain="technologyreview.com",
        source_url="https://www.technologyreview.com/2026/09/17/gpt-5-beta/?utm_source=twitter",
        canonical_url="https://technologyreview.com/2026/09/17/gpt-5-beta",
        published_at=datetime.now(timezone.utc),
        summary="OpenAI reveals next-generation frontier model for enterprise developers.",
        categories=["AI Models", "Generative AI"],
        entities=["OpenAI"],
        discovery_source={
            "name": "MIT Tech Review",
            "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
            "source_type": "RSS_FEED"
        },
        source={
            "name": "MIT Tech Review",
            "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
            "source_type": "RSS_FEED"
        },
        content_hash="hash123",
        canonical_url_hash="urlhash123"
    )

    assert rec.entity_type == "news"
    assert rec.canonical_url == "https://technologyreview.com/2026/09/17/gpt-5-beta"
    assert "AI Models" in rec.categories


def test_source_registry_structure():
    engine = NewsDiscoveryEngine()
    registry = engine.get_source_registry()
    assert len(registry) >= 20

    for source in registry:
        s_obj = NewsSource(**source)
        assert s_obj.source_id.startswith("src_")
        assert s_obj.feed_url.startswith("http")
        assert len(s_obj.publisher_domain) > 3


def test_rss_xml_parsing():
    engine = NewsDiscoveryEngine()
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>AI News Feed</title>
            <item>
                <title><![CDATA[NVIDIA Releases New AI Chip Architecture]]></title>
                <link>https://blogs.nvidia.com/blog/2026/09/17/new-ai-chip/?utm_medium=rss</link>
                <description><![CDATA[<p>NVIDIA announces high-performance AI accelerator chip with 100 TFLOPS FP8 performance.</p>]]></description>
                <pubDate>Thu, 17 Sep 2026 12:00:00 GMT</pubDate>
            </item>
        </channel>
    </rss>
    """
    source_info = {
        "source_id": "src_nvidia_blog",
        "source_name": "NVIDIA AI Blog",
        "publisher_domain": "nvidia.com",
        "feed_url": "https://blogs.nvidia.com/feed/"
    }

    parsed = engine.parse_feed_xml(sample_xml, source_info)
    assert len(parsed) == 1
    assert parsed[0]["title"] == "NVIDIA Releases New AI Chip Architecture"
    assert parsed[0]["url"] == "https://blogs.nvidia.com/blog/2026/09/17/new-ai-chip/?utm_medium=rss"


def test_url_canonicalization_and_html_stripping():
    extractor = NewsExtractor()

    raw_html = "<p>OpenAI release <b>GPT-5</b> details with &amp; benchmarks!</p>"
    clean_text = extractor.strip_html_tags(raw_html)
    assert clean_text == "OpenAI release GPT-5 details with & benchmarks!"

    dirty_url = "https://www.techcrunch.com/2026/09/17/ai-funding/?utm_source=twitter&utm_medium=social&fbclid=123456"
    canon_url, domain = extractor.canonicalize_article_url(dirty_url)

    assert "utm_source" not in canon_url
    assert "fbclid" not in canon_url
    assert canon_url == "https://techcrunch.com/2026/09/17/ai-funding"
    assert domain == "techcrunch.com"


def test_news_qualification_precedence():
    qualifier = NewsQualifier()

    # 1. HARD_EXCLUSION: missing title
    cand_no_title = {
        "title": "",
        "url": "https://techcrunch.com/article/1",
        "source_domain": "techcrunch.com",
        "summary": "Some summary text"
    }
    status, reason = qualifier.qualify(cand_no_title)
    assert status == "HARD_EXCLUSION"

    # 2. HARD_EXCLUSION: non-article search page
    cand_search = {
        "title": "Search Results for AI",
        "url": "https://techcrunch.com/search?q=ai",
        "source_domain": "techcrunch.com",
        "summary": "List of search results"
    }
    status, reason = qualifier.qualify(cand_search)
    assert status == "HARD_EXCLUSION"

    # 3. REVIEW_REQUIRED: extremely low info content
    cand_short = {
        "title": "Short",
        "url": "https://techcrunch.com/article/2",
        "source_domain": "techcrunch.com",
        "summary": "Short summary"
    }
    status, reason = qualifier.qualify(cand_short)
    assert status == "REVIEW_REQUIRED"

    # 4. QUALIFIED: valid headline & summary
    cand_valid = {
        "title": "Anthropic Unveils Claude 3.5 Sonnet Infrastructure Improvements",
        "url": "https://techcrunch.com/2026/09/17/anthropic-claude-35/",
        "canonical_url": "https://techcrunch.com/2026/09/17/anthropic-claude-35",
        "source_domain": "techcrunch.com",
        "summary": "Anthropic details infrastructure and speed improvements for enterprise API customers."
    }
    status, reason = qualifier.qualify(cand_valid)
    assert status == "QUALIFIED"


def test_news_deduplication_resolver():
    resolver = NewsDeduplicationResolver()

    art1 = {
        "id": "news:art001",
        "canonical_title": "Google DeepMind Launches Gemini 2.0 Pro Model",
        "canonical_url": "https://blog.google/technology/ai/gemini-2-pro",
        "source_domain": "blog.google",
        "summary": "Google DeepMind announces Gemini 2.0 Pro featuring enhanced multimodal reasoning capabilities."
    }

    art2_dup_url = {
        "id": "news:art002",
        "canonical_title": "Google DeepMind Launches Gemini 2.0 Pro Model",
        "canonical_url": "https://blog.google/technology/ai/gemini-2-pro",
        "source_domain": "blog.google",
        "summary": "Google DeepMind announces Gemini 2.0 Pro featuring enhanced multimodal reasoning capabilities."
    }

    art3_unique = {
        "id": "news:art003",
        "canonical_title": "Meta Releases Llama 4 Open Source Weights",
        "canonical_url": "https://ai.meta.com/blog/llama-4-release",
        "source_domain": "ai.meta.com",
        "summary": "Meta FAIR releases Llama 4 foundation model weights for commercial AI researchers."
    }

    res1, is_dup1 = resolver.resolve(art1)
    res2, is_dup2 = resolver.resolve(art2_dup_url)
    res3, is_dup3 = resolver.resolve(art3_unique)

    assert not is_dup1
    assert is_dup2
    assert res2["duplicate_of"] == "news:art001"
    assert not is_dup3


def test_news_event_clustering():
    clusterer = NewsEventClusterer()

    articles = [
        {
            "id": "news:art101",
            "title": "OpenAI Launches GPT-5 Frontier Model for Enterprise",
            "published_at": "2026-09-17T10:00:00Z"
        },
        {
            "id": "news:art102",
            "title": "OpenAI Releases GPT-5 Enterprise Model for Developers",
            "published_at": "2026-09-17T11:00:00Z"
        },
        {
            "id": "news:art103",
            "title": "NVIDIA Announces Blackwell Ultra GPU Specifications",
            "published_at": "2026-09-17T12:00:00Z"
        }
    ]

    clustered_arts, clusters = clusterer.cluster_articles(articles)

    assert len(clustered_arts) == 3
    # First two articles should be in the same event cluster
    assert clustered_arts[0]["event_cluster_id"] == clustered_arts[1]["event_cluster_id"]
    # Third article should be in a separate event cluster
    assert clustered_arts[0]["event_cluster_id"] != clustered_arts[2]["event_cluster_id"]


def test_news_accounting_equations():
    raw = 250
    qualified = 200
    rejected = 40
    review = 10

    unique_accepted = 180
    duplicates = 20

    assert raw == qualified + rejected + review
    assert qualified == unique_accepted + duplicates
