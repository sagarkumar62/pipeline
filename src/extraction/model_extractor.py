from typing import Dict, Any
from src.extraction.base import BaseExtractor
from src.models.model import ModelRecord
from src.models.base import DiscoverySource, EvidenceSource


class ModelExtractor(BaseExtractor):
    """
    Extractor for Model entities from OpenRouter API, Hugging Face, and GitHub sources.
    Extracts structured Model metadata fields while preserving provenance.
    """

    def extract(self, raw_item: Dict[str, Any], source_name: str = "Model Discovery Source") -> Dict[str, Any]:
        src_name = raw_item.get("_discovery_source") or source_name
        query = raw_item.get("_discovery_query") or "https://openrouter.ai/api/v1/models"

        name = ""
        provider = None
        huggingface_id = None
        repository_url = None
        official_url = None
        description = raw_item.get("description") or ""
        context_window = None
        architecture = None
        license_str = None
        modality = ["text"]
        model_type = "Large Language Model"
        model_family = None
        version = None
        quantization = None
        base_model = None
        fine_tuned_from = None
        providers = []

        if src_name == "OpenRouter API":
            or_id = str(raw_item.get("id") or "")
            or_name = str(raw_item.get("name") or "")
            name = or_name if or_name else or_id

            if "/" in or_id:
                parts = or_id.split("/")
                provider = parts[0].capitalize()
                huggingface_id = or_id
            
            context_window = raw_item.get("context_length")
            arch_dict = raw_item.get("architecture") or {}
            if isinstance(arch_dict, dict):
                mod_str = arch_dict.get("modality")
                if mod_str:
                    if "image" in mod_str or "multimodal" in mod_str:
                        modality = ["text", "image"]
                        model_type = "Vision-Language Model"
                    elif "audio" in mod_str:
                        modality = ["text", "audio"]
                        model_type = "Audio Model"

            # Parse provider / family from name
            name_lower = name.lower()
            if "llama" in name_lower:
                model_family = "Llama"
            elif "gpt" in name_lower:
                model_family = "GPT"
            elif "claude" in name_lower:
                model_family = "Claude"
            elif "mistral" in name_lower:
                model_family = "Mistral"
            elif "qwen" in name_lower:
                model_family = "Qwen"
            elif "deepseek" in name_lower:
                model_family = "DeepSeek"
            elif "gemini" in name_lower:
                model_family = "Gemini"

            official_url = f"https://openrouter.ai/models/{or_id}"

        elif src_name == "HuggingFace Models API":
            hf_id = str(raw_item.get("id") or raw_item.get("modelId") or "")
            name = hf_id.split("/")[-1] if "/" in hf_id else hf_id
            if "/" in hf_id:
                provider = hf_id.split("/")[0]
            huggingface_id = hf_id
            official_url = f"https://huggingface.co/{hf_id}"

            tags = raw_item.get("tags") or []
            if isinstance(tags, list):
                if any("gguf" in str(t).lower() for t in tags):
                    quantization = "GGUF"
                if any("gptq" in str(t).lower() for t in tags):
                    quantization = "GPTQ"
                if any("awq" in str(t).lower() for t in tags):
                    quantization = "AWQ"

            # Extract base model tag if available
            pipeline = str(raw_item.get("pipeline_tag") or "").lower()
            if "image-to-text" in pipeline or "visual-question-answering" in pipeline:
                modality = ["text", "image"]
                model_type = "Vision-Language Model"
            elif "text-to-image" in pipeline:
                modality = ["text", "image"]
                model_type = "Image Generation Model"

        else: # GitHub Model Search
            owner_info = raw_item.get("owner")
            owner = owner_info.get("login", "") if isinstance(owner_info, dict) else str(owner_info or "").strip()
            name = (raw_item.get("name") or "").strip()
            repository_url = raw_item.get("html_url") or f"https://github.com/{owner}/{name}"
            official_url = raw_item.get("homepage")
            provider = owner
            license_info = raw_item.get("license")
            if isinstance(license_info, dict):
                license_str = license_info.get("spdx_id") or license_info.get("name")

        # Fallback name validation
        if not name:
            name = "Unnamed Model"

        primary_url = official_url or repository_url or f"https://openrouter.ai/models/{name}"

        discovery_src = DiscoverySource(
            name=src_name,
            url=query,
            source_type="API",
            source_trust_level="HIGH"
        )

        evidence_src = EvidenceSource(
            url=primary_url,
            source_type="OFFICIAL_WEBSITE" if official_url else "GITHUB_REPOSITORY",
            trust_level="HIGH",
            evidence_type="WEBSITE_META" if official_url else "CODE_REPOSITORY"
        )

        extracted = {
            "name": name,
            "model_name": name,
            "provider": provider,
            "huggingface_id": huggingface_id,
            "url": primary_url,
            "repository_url": repository_url,
            "official_url": official_url,
            "description": description,
            "categories": ["AI Model", model_type],
            "model_type": model_type,
            "model_family": model_family,
            "context_window": context_window,
            "modality": modality,
            "quantization": quantization,
            "license": license_str,
            "discovery_source": discovery_src,
            "source": discovery_src,
            "evidence_sources": [evidence_src]
        }
        return extracted

    def to_record(self, raw_item: Dict[str, Any], source_name: str = "Model Discovery Source") -> ModelRecord:
        extracted = self.extract(raw_item, source_name)
        return ModelRecord.create_canonical(**extracted)
