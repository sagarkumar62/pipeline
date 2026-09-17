import pytest
from src.models.tool import ToolRecord, SourceMetadata
from src.utils.urls import normalize_url, extract_domain
from src.utils.hashing import generate_tool_id


def test_url_normalization():
    raw_url = "HTTPS://WWW.Example.com/product/page/?utm_source=twitter&utm_medium=social&ref=123#pricing"
    expected = "https://example.com/product/page"
    assert normalize_url(raw_url) == expected


def test_domain_extraction():
    url = "https://sub.domain.openai.com/v1/models"
    assert extract_domain(url) == "sub.domain.openai.com"


def test_deterministic_tool_id_stability():
    id1 = generate_tool_id("openai.com", "ChatGPT")
    id2 = generate_tool_id("openai.com", "ChatGPT")
    id3 = generate_tool_id("openai.com", "chatgpt")
    
    assert id1 == id2
    assert id1 == id3
    assert id1.startswith("tool_")
    
    # Different tool name or domain yields different ID
    id_other = generate_tool_id("anthropic.com", "Claude")
    assert id1 != id_other


def test_tool_record_creation():
    record = ToolRecord.create_canonical(
        name="ChatGPT",
        url="https://chatgpt.com/?utm_source=google",
        source_name="GitHub API",
        source_url="https://github.com/openai/chatgpt",
        description="An AI assistant developed by OpenAI.",
        categories=["Productivity", "AI Assistants"],
        company_name="OpenAI",
        company_url="https://openai.com"
    )

    assert record.entity_type == "TOOL"
    assert record.name == "ChatGPT"
    assert record.url == "https://chatgpt.com"
    assert record.source.name == "GitHub API"
    assert record.source.url == "https://github.com/openai/chatgpt"
    assert record.company_name == "OpenAI"
    assert record.company_url == "https://openai.com"
    assert record.id.startswith("tool_")
    assert record.quality_score == 0.0
