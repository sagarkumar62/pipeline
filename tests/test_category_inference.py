"""Tests for evidence-based category inference."""

import pytest
from src.classification.classifier import TaxonomyClassifier


@pytest.fixture
def classifier():
    return TaxonomyClassifier()


class TestCategoryInference:
    """Test category inference from topics, description, and name."""

    def test_mcp_topic_infers_mcp_category(self, classifier):
        """MCP topics should infer MCP category."""
        record = {
            "categories": [],
            "github_topics": ["mcp", "mcp-server", "llm"],
            "description": "MCP server for AI assistant integration",
            "name": "my-mcp-server",
        }
        result = classifier.classify(record)
        assert "MCP" in result["categories"]

    def test_developer_tool_topic(self, classifier):
        """Developer tool topics should infer Developer Tools category."""
        record = {
            "categories": [],
            "github_topics": ["developer-tools", "cli", "api"],
            "description": "A command-line tool for developers",
            "name": "dev-cli",
        }
        result = classifier.classify(record)
        assert "Developer Tools" in result["categories"]

    def test_creative_tool_from_description(self, classifier):
        """Image generation keywords in description should infer Image Generation."""
        record = {
            "categories": [],
            "github_topics": [],
            "description": "A text-to-image generation model using stable diffusion",
            "name": "art-gen",
        }
        result = classifier.classify(record)
        assert "Image Generation" in result["categories"]

    def test_multiple_categories_supported(self, classifier):
        """Multiple valid categories should be preserved."""
        record = {
            "categories": [],
            "github_topics": ["mcp", "automation", "developer-tools"],
            "description": "MCP server for workflow automation",
            "name": "mcp-auto",
        }
        result = classifier.classify(record)
        assert len(result["categories"]) >= 2

    def test_insufficient_evidence_fallback(self, classifier):
        """No matching topics or description → fallback to Developer Tools."""
        record = {
            "categories": [],
            "github_topics": [],
            "description": "A useful utility",
            "name": "myutil",
        }
        result = classifier.classify(record)
        assert "Developer Tools" in result["categories"]

    def test_existing_valid_categories_preserved(self, classifier):
        """Pre-existing valid categories should not be overwritten."""
        record = {
            "categories": ["Audio"],
            "github_topics": ["developer-tools"],
            "description": "Text-to-speech engine",
            "name": "tts-engine",
        }
        result = classifier.classify(record)
        assert "Audio" in result["categories"]

    def test_agent_topic_infers_agents(self, classifier):
        """Agent topics should infer Agents category."""
        record = {
            "categories": [],
            "github_topics": ["ai-agent", "multi-agent"],
            "description": "Framework for building autonomous AI agents",
            "name": "agent-framework",
        }
        result = classifier.classify(record)
        assert "Agents" in result["categories"]

    def test_audio_topic_infers_audio(self, classifier):
        """Audio/TTS topics should infer Audio category."""
        record = {
            "categories": [],
            "github_topics": ["tts", "text-to-speech"],
            "description": "Text-to-speech synthesis engine",
            "name": "voice-gen",
        }
        result = classifier.classify(record)
        assert "Audio" in result["categories"]

    def test_video_description_infers_video(self, classifier):
        """Video generation description should infer Video category."""
        record = {
            "categories": [],
            "github_topics": [],
            "description": "AI-powered video generation and editing platform",
            "name": "vid-gen",
        }
        result = classifier.classify(record)
        assert "Video" in result["categories"]

    def test_inference_reasons_tracked(self, classifier):
        """Category inference reasons should be stored."""
        record = {
            "categories": [],
            "github_topics": ["mcp"],
            "description": "MCP server",
            "name": "mcp-test",
        }
        result = classifier.classify(record)
        assert "category_inference_reasons" in result
        assert len(result["category_inference_reasons"]) > 0

    def test_automation_topic(self, classifier):
        """Automation topics should infer Automation category."""
        record = {
            "categories": [],
            "github_topics": ["automation", "workflow"],
            "description": "Workflow automation tool",
            "name": "auto-flow",
        }
        result = classifier.classify(record)
        assert "Automation" in result["categories"]

    def test_models_topic(self, classifier):
        """LLM/model topics should infer Models category."""
        record = {
            "categories": [],
            "github_topics": ["llm", "language-model", "fine-tuning"],
            "description": "Large language model serving",
            "name": "model-server",
        }
        result = classifier.classify(record)
        assert "Models" in result["categories"]
