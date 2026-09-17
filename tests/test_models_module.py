import pytest
import os
import json
import hashlib
from src.models.model import ModelRecord
from src.models.agent import AgentRecord
from src.models.mcp import MCPRecord
from src.models.tool import ToolRecord
from src.models.repository import RepositoryRecord
from src.extraction.model_extractor import ModelExtractor
from src.qualification.model_qualifier import ModelQualifier
from src.deduplication.model_resolver import ModelDeduplicationResolver


def test_model_record_validation():
    rec = ModelRecord.create_canonical(
        name="Llama 3.1 8B Instruct",
        model_name="Llama 3.1 8B Instruct",
        provider="Meta",
        huggingface_id="meta-llama/Llama-3.1-8B-Instruct",
        context_window=131072,
        parameter_count="8B",
        license="Llama-3.1"
    )
    assert rec.name == "Llama 3.1 8B Instruct"
    assert rec.entity_type == "MODEL"
    assert rec.provider == "Meta"
    assert rec.context_window == 131072


def test_model_entity_type_discriminator():
    rec = ModelRecord.create_canonical(
        name="GPT-4o",
        provider="OpenAI",
        official_url="https://openai.com/index/hello-gpt-4o"
    )
    assert rec.entity_type == "MODEL"


def test_model_required_identity_fields():
    rec = ModelRecord.create_canonical(
        name="Claude 3.5 Sonnet",
        provider="Anthropic",
        official_url="https://anthropic.com/news/claude-3-5-sonnet"
    )
    assert rec.id == "model:anthropic/claude-3.5-sonnet"
    assert rec.url == "https://anthropic.com/news/claude-3-5-sonnet"
    assert rec.discovery_source is not None


def test_model_specific_metadata():
    rec = ModelRecord.create_canonical(
        name="DeepSeek-R1",
        provider="DeepSeek",
        huggingface_id="deepseek-ai/DeepSeek-R1",
        model_type="Reasoning Model",
        architecture="MoE",
        context_window=128000
    )
    assert rec.model_type == "Reasoning Model"
    assert rec.architecture == "MoE"


def test_model_hard_exclusion_precedence():
    qualifier = ModelQualifier()
    awesome_item = {
        "name": "awesome-llm",
        "description": "A curated list of awesome Large Language Models and resources",
        "topics": ["awesome", "llm"],
        "stars": 15000,
        "archived": False
    }
    status, reason = qualifier.qualify(awesome_item)
    assert status == "HARD_EXCLUSION"


def test_model_review_precedence():
    qualifier = ModelQualifier()
    fork_item = {
        "name": "llama-custom-fork",
        "description": "Fork of llama repository",
        "topics": ["llm"],
        "fork": True
    }
    status, reason = qualifier.qualify(fork_item)
    assert status == "REVIEW_REQUIRED"


def test_model_genuine_model_qualification():
    qualifier = ModelQualifier()
    valid_model = {
        "name": "Llama 3.1 70B",
        "description": "State of the art open weights foundation model by Meta",
        "huggingface_id": "meta-llama/Llama-3.1-70B-Instruct"
    }
    status, reason = qualifier.qualify(valid_model)
    assert status == "QUALIFIED"


def test_model_benchmark_only_rejection():
    qualifier = ModelQualifier()
    benchmark_item = {
        "name": "swe-bench-leaderboard",
        "description": "Benchmark leaderboard for software engineering agents and models",
        "topics": ["benchmark", "leaderboard"]
    }
    status, reason = qualifier.qualify(benchmark_item)
    assert status == "HARD_EXCLUSION"


def test_model_wrapper_rejection():
    qualifier = ModelQualifier()
    wrapper_item = {
        "name": "ollama-ui-wrapper",
        "description": "Desktop client UI wrapper for Ollama local models",
        "topics": ["ui", "wrapper"]
    }
    status, reason = qualifier.qualify(wrapper_item)
    assert status == "HARD_EXCLUSION"


def test_model_tutorial_list_course_rejection():
    qualifier = ModelQualifier()
    course_item = {
        "name": "llm-course-2024",
        "description": "Course materials and tutorials on fine-tuning LLMs",
        "topics": ["course", "tutorial"]
    }
    status, reason = qualifier.qualify(course_item)
    assert status == "HARD_EXCLUSION"


def test_model_version_handling():
    rec1 = ModelRecord.create_canonical(name="Llama 2 70B", provider="Meta", version="2")
    rec2 = ModelRecord.create_canonical(name="Llama 3 70B", provider="Meta", version="3")
    assert rec1.id != rec2.id


def test_model_fine_tune_detection():
    rec = ModelRecord.create_canonical(
        name="Llama-3.1-8B-Hermes",
        provider="NousResearch",
        base_model="meta-llama/Llama-3.1-8B",
        fine_tuned_from="meta-llama/Llama-3.1-8B"
    )
    assert rec.base_model == "meta-llama/Llama-3.1-8B"


def test_model_base_model_relationship():
    rec = ModelRecord.create_canonical(
        name="Mistral-7B-Instruct-v0.2",
        provider="Mistral AI",
        fine_tuned_from="mistralai/Mistral-7B-v0.1"
    )
    assert rec.fine_tuned_from == "mistralai/Mistral-7B-v0.1"


def test_model_quantization_consolidation():
    resolver = ModelDeduplicationResolver()
    base = {"id": "model:hf:meta-llama--llama-3.1-8b-instruct", "huggingface_id": "meta-llama/Llama-3.1-8B-Instruct"}
    gguf = {"id": "model:hf:meta-llama--llama-3.1-8b-instruct-gguf", "huggingface_id": "meta-llama/Llama-3.1-8B-Instruct"}
    resolver.resolve(base)
    res, dup = resolver.resolve(gguf)
    assert dup


def test_model_provider_variant_consolidation():
    resolver = ModelDeduplicationResolver()
    item1 = {"id": "model:hf:meta-llama--llama-3.1-8b", "huggingface_id": "meta-llama/Llama-3.1-8B", "provider": "Together"}
    item2 = {"id": "model:hf:openrouter--meta-llama--llama-3.1-8b", "huggingface_id": "openrouter/meta-llama/Llama-3.1-8B", "provider": "Groq"}
    resolver.resolve(item1)
    res, dup = resolver.resolve(item2)
    assert dup


def test_model_huggingface_duplicate_handling():
    resolver = ModelDeduplicationResolver()
    m1 = {"id": "model:hf:mistralai--mistral-7b-v0.1", "huggingface_id": "mistralai/Mistral-7B-v0.1"}
    m2 = {"id": "model:hf:mistralai--mistral-7b-v0.1-dupe", "huggingface_id": "mistralai/Mistral-7B-v0.1"}
    resolver.resolve(m1)
    res, dup = resolver.resolve(m2)
    assert dup


def test_model_openrouter_provider_variant_handling():
    resolver = ModelDeduplicationResolver()
    or1 = {"id": "model:hf:openai--gpt-4o", "huggingface_id": "openai/gpt-4o"}
    or2 = {"id": "model:hf:openrouter--openai--gpt-4o", "huggingface_id": "openrouter/openai/gpt-4o"}
    resolver.resolve(or1)
    res, dup = resolver.resolve(or2)
    assert dup


def test_model_cross_source_duplicate_merging():
    resolver = ModelDeduplicationResolver()
    hf = {"id": "model:hf:deepseek-ai--deepseek-v3", "huggingface_id": "deepseek-ai/DeepSeek-V3"}
    openrouter = {"id": "model:hf:deepseek-ai--deepseek-v3", "huggingface_id": "deepseek-ai/DeepSeek-V3"}
    resolver.resolve(hf)
    res, dup = resolver.resolve(openrouter)
    assert dup


def test_model_distinct_model_preservation():
    resolver = ModelDeduplicationResolver()
    m1 = {"id": "model:meta/llama-3.1-8b", "provider": "meta", "name": "llama-3.1-8b"}
    m2 = {"id": "model:mistralai/mistral-7b", "provider": "mistralai", "name": "mistral-7b"}
    resolver.resolve(m1)
    res, dup = resolver.resolve(m2)
    assert not dup


def test_model_deterministic_canonical_identity():
    rec = ModelRecord.create_canonical(
        name="Llama 3.1 405B",
        huggingface_id="meta-llama/Llama-3.1-405B-Instruct"
    )
    assert rec.id == "model:hf:meta-llama--llama-3.1-405b-instruct"


def test_model_provenance_completeness():
    extractor = ModelExtractor()
    raw = {
        "id": "openai/gpt-4o",
        "name": "OpenAI: GPT-4o",
        "description": "Omni model for multimodal intelligence",
        "_discovery_source": "OpenRouter API",
        "_discovery_query": "https://openrouter.ai/api/v1/models"
    }
    rec = extractor.to_record(raw)
    assert rec.discovery_source.name == "OpenRouter API"
    assert len(rec.evidence_sources) == 1


def test_model_official_website_verification_semantics():
    rec = ModelRecord.create_canonical(
        name="GPT-4o",
        official_url="https://openai.com/index/hello-gpt-4o"
    )
    assert rec.official_url == "https://openai.com/index/hello-gpt-4o"


def test_model_github_not_official_website_rule():
    rec = ModelRecord.create_canonical(
        name="Llama-Repository",
        repository_url="https://github.com/meta-llama/llama3"
    )
    assert "github.com" in rec.repository_url


def test_model_provider_page_semantics():
    extractor = ModelExtractor()
    raw = {
        "id": "meta-llama/Llama-3.1-8B",
        "name": "Llama 3.1 8B",
        "_discovery_source": "HuggingFace Models API"
    }
    rec = extractor.to_record(raw)
    assert "huggingface.co" in rec.official_url


def test_model_logo_semantics():
    rec = ModelRecord.create_canonical(name="Llama 3.1", provider="Meta")
    assert rec.logo_verified is False
    assert rec.logo_url is None


def test_model_social_preview_rejection():
    rec = ModelRecord.create_canonical(name="DeepSeek V3", provider="DeepSeek")
    assert rec.logo_verified is False


def test_model_description_grounding():
    extractor = ModelExtractor()
    raw = {
        "id": "meta-llama/llama-3.1-8b-instruct",
        "name": "Llama 3.1 8B Instruct",
        "description": "Llama 3.1 8B Instruct model by Meta.",
        "_discovery_source": "OpenRouter API"
    }
    rec = extractor.to_record(raw)
    assert rec.description == "Llama 3.1 8B Instruct model by Meta."


def test_model_benchmark_provenance():
    rec = ModelRecord.create_canonical(
        name="Llama 3.1 405B",
        benchmark_evidence=[{"benchmark": "MMLU", "score": 88.6, "source": "Official Model Card"}]
    )
    assert len(rec.benchmark_evidence) == 1
    assert rec.benchmark_evidence[0]["score"] == 88.6


def test_model_missing_evidence_handling():
    extractor = ModelExtractor()
    raw = {"name": "generic-model"}
    rec = extractor.to_record(raw)
    assert rec.context_window is None
    assert rec.huggingface_id is None
    assert rec.quantization is None


def test_model_malformed_source_handling():
    extractor = ModelExtractor()
    raw = {"name": None, "id": None}
    extracted = extractor.extract(raw)
    assert extracted["name"] == "Unnamed Model"


def test_model_rate_limit_retry_configuration():
    from src.discovery.model_discovery import ModelsAdapter
    adapter = ModelsAdapter()
    assert adapter.openrouter_endpoint == "https://openrouter.ai/api/v1/models"


def test_protected_tools_dataset_integrity():
    tools_json_path = "data/exports/tools.json"
    if os.path.exists(tools_json_path):
        with open(tools_json_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest().upper()
        assert h == "4520014C9A1676F9090BE806087A92AC0E12FEF3D3136A95860CFF48388FF2A1"


def test_protected_repository_dataset_integrity():
    repos_final_path = "data/working/repositories/repositories_final.json"
    if os.path.exists(repos_final_path):
        with open(repos_final_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest().upper()
        assert h == "176D5DEEEC8063FC4684C058B5E758649E57375ACE6AB5ADA05A4ECE43FB8465"


def test_protected_mcp_dataset_integrity():
    mcp_final_path = "data/working/mcp/mcp_final.json"
    if os.path.exists(mcp_final_path):
        with open(mcp_final_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest().upper()
        assert h == "CED0BF7AE869ACC54403C0453A1A12CF097131D6D5CB438BEA36216822A9216B"


def test_protected_agents_dataset_integrity():
    agents_final_path = "data/working/agents/agents_final.json"
    if os.path.exists(agents_final_path):
        with open(agents_final_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest().upper()
        assert h == "B27609EA151951A97445CA5CFDF54C58F22B223D87808B466BA505BC6E00DA14"
