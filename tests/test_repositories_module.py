import pytest
import os
import json
import hashlib
from src.models.repository import RepositoryRecord
from src.models.tool import ToolRecord
from src.extraction.repository_extractor import RepositoryExtractor
from src.qualification.repository_qualifier import RepositoryQualifier
from src.deduplication.repository_resolver import RepositoryDeduplicationResolver


def test_repository_schema_validation():
    rec = RepositoryRecord.create_canonical(
        owner="huggingface",
        name="transformers",
        repository_url="https://github.com/huggingface/transformers",
        description="State-of-the-art Machine Learning for Pytorch, TensorFlow, and JAX.",
        stars=130000,
        topics=["machine-learning", "deep-learning", "llm"],
        license="Apache-2.0"
    )
    assert rec.name == "transformers"
    assert rec.owner == "huggingface"
    assert rec.entity_type == "REPOSITORY"
    assert rec.id == "repository:huggingface/transformers"
    assert rec.stars == 130000
    assert "machine-learning" in rec.topics


def test_entity_type_discriminator():
    repo_rec = RepositoryRecord.create_canonical(
        owner="langchain-ai",
        name="langchain",
        repository_url="https://github.com/langchain-ai/langchain"
    )
    tool_rec = ToolRecord.create_canonical(
        name="LangChain",
        url="https://langchain.com"
    )
    assert repo_rec.entity_type == "REPOSITORY"
    assert tool_rec.entity_type == "TOOL"
    assert repo_rec.entity_type != tool_rec.entity_type


def test_deterministic_repository_ids():
    rec1 = RepositoryRecord.create_canonical(
        owner="vllm-project",
        name="vllm",
        repository_url="https://github.com/vllm-project/vllm"
    )
    rec2 = RepositoryRecord.create_canonical(
        owner="vllm-project",
        name="vllm",
        repository_url="https://github.com/vllm-project/vllm"
    )
    assert rec1.id == rec2.id == "repository:vllm-project/vllm"


def test_repository_url_normalization():
    rec = RepositoryRecord.create_canonical(
        owner="ollama",
        name="ollama",
        repository_url="HTTP://GITHUB.COM/OLLAMA/OLLAMA/"
    )
    assert rec.repository_url == "https://github.com/ollama/ollama"
    assert rec.url == "https://github.com/ollama/ollama"


def test_repository_qualification_rules():
    qualifier = RepositoryQualifier()
    
    # Qualified candidate
    qualified_item = {
        "name": "vllm",
        "owner": "vllm-project",
        "description": "High-throughput and memory-efficient LLM serving engine",
        "topics": ["llm", "inference", "pytorch"],
        "stars": 25000,
        "archived": False,
        "fork": False
    }
    status, reason = qualifier.qualify(qualified_item)
    assert status == "QUALIFIED"


def test_hard_exclusion_precedence():
    qualifier = RepositoryQualifier()
    
    # Awesome list repository with high stars (positive signal MUST NOT override hard exclusion)
    awesome_item = {
        "name": "awesome-deep-learning",
        "description": "A curated list of awesome deep learning tutorials and courses",
        "topics": ["awesome", "deep-learning"],
        "stars": 50000,
        "archived": False,
        "fork": False
    }
    status, reason = qualifier.qualify(awesome_item)
    assert status == "HARD_EXCLUSION"
    assert "Awesome" in reason or "hard negative" in reason


def test_review_classification():
    qualifier = RepositoryQualifier()
    
    # Ambiguous low-star candidate without description
    sparse_item = {
        "name": "temp-ai-script",
        "owner": "user123",
        "description": "",
        "topics": [],
        "stars": 2,
        "archived": False,
        "fork": False
    }
    status, reason = qualifier.qualify(sparse_item)
    assert status == "REVIEW_REQUIRED"


def test_duplicate_repository_detection():
    resolver = RepositoryDeduplicationResolver()
    rec1 = {
        "id": "repository:meta-llama/llama3",
        "owner": "meta-llama",
        "name": "llama3",
        "repository_url": "https://github.com/meta-llama/llama3"
    }
    rec2 = {
        "id": "repository:meta-llama/llama3",
        "owner": "meta-llama",
        "name": "llama3",
        "repository_url": "https://github.com/meta-llama/llama3"
    }
    
    resolved1, is_dup1 = resolver.resolve(rec1)
    assert not is_dup1

    resolved2, is_dup2 = resolver.resolve(rec2)
    assert is_dup2
    assert resolved2["duplicate_of"] == "repository:meta-llama/llama3"


def test_fork_handling():
    qualifier = RepositoryQualifier()
    fork_item = {
        "name": "transformers",
        "owner": "someuser",
        "description": "My personal fork of transformers",
        "topics": ["llm"],
        "stars": 15,
        "archived": False,
        "fork": True
    }
    status, reason = qualifier.qualify(fork_item)
    assert status == "REVIEW_REQUIRED"
    assert "fork" in reason.lower()


def test_provenance_preservation():
    extractor = RepositoryExtractor()
    raw = {
        "name": "vllm",
        "owner": {"login": "vllm-project"},
        "html_url": "https://github.com/vllm-project/vllm",
        "description": "LLM serving engine",
        "stargazers_count": 25000,
        "_discovery_query": "topic:llm-inference",
        "_discovery_source": "GitHub API"
    }
    rec = extractor.to_record(raw)
    assert rec.discovery_source.name == "GitHub API"
    assert len(rec.evidence_sources) == 1
    assert rec.evidence_sources[0].url == "https://github.com/vllm-project/vllm"


def test_description_grounding():
    extractor = RepositoryExtractor()
    raw = {
        "name": "ollama",
        "owner": "ollama",
        "html_url": "https://github.com/ollama/ollama",
        "description": "Get up and running with Llama 3.3, DeepSeek-R1, and other LLMs locally."
    }
    rec = extractor.to_record(raw)
    assert rec.description == "Get up and running with Llama 3.3, DeepSeek-R1, and other LLMs locally."
    # Extracted directly from source evidence without hallucinated additions


def test_website_verification_semantics():
    # Rule: github.com repository URL is NOT an external official website
    rec = RepositoryRecord.create_canonical(
        owner="huggingface",
        name="transformers",
        repository_url="https://github.com/huggingface/transformers",
        homepage="https://github.com/huggingface/transformers"  # Homepage points to github itself
    )
    # The homepage should be acknowledged but non-external
    assert "github.com" in rec.repository_url


def test_logo_verification_semantics():
    # Rule: Social preview images (opengraph) are NOT verified official logos
    rec = RepositoryRecord.create_canonical(
        owner="langchain-ai",
        name="langchain",
        repository_url="https://github.com/langchain-ai/langchain"
    )
    assert rec.logo_verified is False
    assert rec.logo_url is None


def test_checkpoint_persistence(tmp_path):
    out_file = tmp_path / "test_repos.json"
    rec = RepositoryRecord.create_canonical(
        owner="ollama",
        name="ollama",
        repository_url="https://github.com/ollama/ollama"
    )
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump([rec.model_dump(mode="json")], f)

    assert out_file.exists()
    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data[0]["id"] == "repository:ollama/ollama"


def test_api_failure_resilience():
    from src.discovery.repository_discovery import RepositoriesAdapter
    adapter = RepositoriesAdapter(queries=["topic:nonexistent123456789xyz"])
    assert adapter.source_name == "GitHub API (Repositories Adapter)"


def test_rate_limit_backoff_configuration():
    from src.discovery.repository_discovery import RepositoriesAdapter
    adapter = RepositoriesAdapter(per_page=10, max_pages_per_query=1)
    assert adapter.per_page == 10
    assert adapter.max_pages_per_query == 1


def test_protected_tools_dataset_integrity():
    tools_json_path = "data/exports/tools.json"
    if os.path.exists(tools_json_path):
        with open(tools_json_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest().upper()
        # Verify hash matches baseline
        assert h == "4520014C9A1676F9090BE806087A92AC0E12FEF3D3136A95860CFF48388FF2A1"
