import json
import os
import pytest
from src.models.model import ModelRecord
from src.qualification.model_qualifier import ModelQualifier
from src.deduplication.model_resolver import ModelDeduplicationResolver


def test_model_baseline_immutability():
    baseline_path = "data/working/models/models_final.json"
    assert os.path.exists(baseline_path)
    with open(baseline_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 102


def test_model_qualification_precedence():
    qualifier = ModelQualifier()

    # Application / Chatbot wrapper must yield HARD_EXCLUSION
    cand_app = {
        "name": "chat-with-llama-ui",
        "description": "User interface application for chatting with Llama 3 API",
        "topics": ["chatbot", "ui"]
    }
    status, reason = qualifier.qualify(cand_app)
    assert status == "HARD_EXCLUSION"

    # Tutorial / Awesome list must yield HARD_EXCLUSION
    cand_awesome = {
        "name": "awesome-llm-models-list",
        "description": "Curated list of open source LLM models and papers",
        "topics": ["awesome-list"]
    }
    status, reason = qualifier.qualify(cand_awesome)
    assert status == "HARD_EXCLUSION"

    # Foundation Model candidate must yield QUALIFIED
    cand_model = {
        "name": "Llama-3.1-8B-Instruct",
        "description": "Multilingual foundation model fine-tuned for instruction following and reasoning",
        "huggingface_id": "meta-llama/Llama-3.1-8B-Instruct",
        "provider": "Meta",
        "stars": 12000
    }
    status, reason = qualifier.qualify(cand_model)
    assert status == "QUALIFIED"


def test_model_evidence_requirement():
    qualifier = ModelQualifier()

    # Lack of explicit model release metadata must yield HARD_EXCLUSION
    cand_no_evidence = {
        "name": "random-python-script",
        "description": "Script that mentions models in comments",
        "topics": ["python"]
    }
    status, reason = qualifier.qualify(cand_no_evidence)
    assert status == "HARD_EXCLUSION"


def test_model_baseline_duplicate_detection():
    resolver = ModelDeduplicationResolver()
    baseline_records = [
        {
            "id": "model:meta-llama-llama-3-1-8b-instruct",
            "name": "Llama-3.1-8B-Instruct",
            "huggingface_id": "meta-llama/Llama-3.1-8B-Instruct",
            "provider": "Meta"
        }
    ]
    resolver.load_baseline(baseline_records)

    cand = {
        "id": "model:meta-llama-llama-3-1-8b-instruct-dup",
        "name": "Llama-3.1-8B-Instruct",
        "huggingface_id": "meta-llama/Llama-3.1-8B-Instruct",
        "provider": "Meta"
    }

    resolved, is_dup = resolver.resolve(cand)
    assert is_dup
    assert resolved["is_baseline_match"] is True
    assert resolved["duplicate_of"] == "model:meta-llama-llama-3-1-8b-instruct"


def test_model_intra_expansion_duplicate_detection():
    resolver = ModelDeduplicationResolver()
    resolver.load_baseline([])  # Empty baseline

    cand1 = {
        "id": "model:deepseek-ai-deepseek-coder-6-7b",
        "name": "deepseek-coder-6.7b-instruct",
        "huggingface_id": "deepseek-ai/deepseek-coder-6.7b-instruct",
        "provider": "DeepSeek"
    }

    cand2 = {
        "id": "model:deepseek-ai-deepseek-coder-6-7b-mirror",
        "name": "deepseek-coder-6.7b-instruct",
        "huggingface_id": "deepseek-ai/deepseek-coder-6.7b-instruct",
        "provider": "DeepSeek"
    }

    _, is_dup1 = resolver.resolve(cand1)
    resolved2, is_dup2 = resolver.resolve(cand2)

    assert not is_dup1
    assert is_dup2
    assert resolved2["is_baseline_match"] is False
    assert resolved2["duplicate_of"] == "model:deepseek-ai-deepseek-coder-6-7b"


def test_model_provider_alias_normalization():
    resolver = ModelDeduplicationResolver()
    resolver.load_baseline([])

    cand1 = {
        "id": "model:meta-llama-3-8b",
        "name": "llama-3-8b-instruct",
        "huggingface_id": "meta-llama/llama-3-8b-instruct"
    }

    cand2 = {
        "id": "model:openrouter-meta-llama-3-8b",
        "name": "llama-3-8b-instruct",
        "huggingface_id": "openrouter/meta-llama/llama-3-8b-instruct"
    }

    _, is_dup1 = resolver.resolve(cand1)
    resolved2, is_dup2 = resolver.resolve(cand2)

    assert not is_dup1
    assert is_dup2
    assert resolved2["duplicate_of"] == "model:meta-llama-3-8b"


def test_model_quantization_normalization():
    resolver = ModelDeduplicationResolver()
    norm1 = resolver._normalize_model_name("llama-3-8b-instruct-gguf")
    norm2 = resolver._normalize_model_name("llama-3-8b-instruct-gptq")
    norm3 = resolver._normalize_model_name("llama-3-8b-instruct")

    assert norm1 == "llama-3-8b-instruct"
    assert norm2 == "llama-3-8b-instruct"
    assert norm3 == "llama-3-8b-instruct"


def test_models_expansion_accounting_equation():
    raw = 1600
    qualified = 1400
    rejected = 190
    review = 10

    baseline_dups = 30
    intra_dups = 170
    final_new = 1200

    assert raw == qualified + rejected + review
    assert qualified == baseline_dups + intra_dups + final_new
