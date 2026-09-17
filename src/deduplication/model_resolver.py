from typing import Dict, List, Tuple, Any, Optional
from src.utils.logging import setup_logger
from src.utils.urls import normalize_url

logger = setup_logger("model_resolver")


class ModelDeduplicationResolver:
    """
    Deterministic deduplication and entity resolution engine for Model entities.
    
    Enforces the Critical Model Identity Rules:
    - Provider variants (e.g., OpenRouter hosting endpoints) are consolidated into canonical models.
    - Quantization variants (GGUF, GPTQ, AWQ) are consolidated unless trained separately.
    - Distinct model versions (e.g., Llama 2 vs Llama 3) remain distinct canonical models.
    - Fine-tunes preserve base model lineage references.
    
    Resolution Priority:
    1. Exact Registry ID / Stable Entity ID
    2. Exact HuggingFace Model ID
    3. Normalized Repository URL match
    4. Canonical Provider/Family/Version Model Identity pair match
    """

    def __init__(self):
        self._seen_ids: Dict[str, Dict[str, Any]] = {}
        self._hf_id_map: Dict[str, str] = {}           # hf_id -> canonical_id
        self._repo_url_map: Dict[str, str] = {}        # repo_url -> canonical_id
        self._canonical_name_map: Dict[str, str] = {}  # clean_name -> canonical_id
        self._family_version_map: Dict[str, str] = {}  # provider/family/version -> canonical_id

    def _normalize_repo(self, repo_url: str) -> str:
        if not repo_url:
            return ""
        url = repo_url.lower().strip()
        url = url.replace("https://", "").replace("http://", "").replace("github.com/", "")
        if url.endswith(".git"):
            url = url[:-4]
        return url.strip("/")

    def _normalize_model_name(self, name: str) -> str:
        if not name:
            return ""
        n = name.lower().strip()
        for q in ["-gguf", "-gptq", "-awq", "_gguf", "_gptq", "_awq"]:
            if n.endswith(q):
                n = n[:-len(q)]
        return n.strip()

    def load_baseline(self, records: List[Dict[str, Any]]) -> int:
        """Pre-loads existing Model records into deduplication indexes."""
        count = 0
        for r in records:
            rec = dict(r) if isinstance(r, dict) else r.model_dump()
            rec_id = rec.get("id")
            if not rec_id:
                continue

            rec["is_baseline"] = True
            self._seen_ids[rec_id] = rec

            hf_id = (rec.get("huggingface_id") or "").lower().strip()
            if hf_id:
                clean_hf = self._normalize_model_name(hf_id)
                self._hf_id_map[clean_hf] = rec_id

            repo_url = rec.get("repository_url") or rec.get("url")
            if repo_url:
                norm_url = normalize_url(repo_url)
                self._repo_url_map[norm_url] = rec_id

            name = (rec.get("name") or rec.get("model_name") or "").lower().strip()
            clean_name = self._normalize_model_name(name)
            provider = (rec.get("provider") or "").lower().strip()
            if clean_name:
                self._canonical_name_map[f"{provider}:{clean_name}"] = rec_id

            count += 1

        logger.info(f"Loaded {count} baseline Model records into resolver indexes.")
        return count

    def resolve(self, record: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Resolves a candidate Model record against existing indexed Model entities.
        
        Returns:
            Tuple[resolved_record, is_duplicate]
        """
        rec_id = record.get("id")
        hf_id = (record.get("huggingface_id") or "").lower().strip()
        repo_url = record.get("repository_url") or record.get("url") or ""
        norm_url = normalize_url(repo_url) if repo_url else ""
        name = (record.get("name") or record.get("model_name") or "").lower().strip()
        clean_name = self._normalize_model_name(name)
        provider = (record.get("provider") or "").lower().strip()
        name_key = f"{provider}:{clean_name}" if clean_name else ""

        # Normalize Provider Variant Aliases (e.g. openrouter/meta-llama/llama-3 -> meta-llama/llama-3)
        clean_hf = hf_id
        if clean_hf.startswith("openrouter/"):
            clean_hf = clean_hf[11:]
        clean_hf = self._normalize_model_name(clean_hf)

        # 1. Exact Stable ID Match
        if rec_id and rec_id in self._seen_ids:
            canonical = self._seen_ids[rec_id]
            record["duplicate_of"] = canonical["id"]
            record["match_method"] = "exact_stable_id"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate Model found by exact ID: '{rec_id}'")
            return record, True

        # 2. HuggingFace ID Match (Provider & Quantization Variant Consolidation)
        if clean_hf and clean_hf in self._hf_id_map:
            canonical_id = self._hf_id_map[clean_hf]
            canonical = self._seen_ids[canonical_id]
            record["duplicate_of"] = canonical_id
            record["match_method"] = "exact_huggingface_id"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)

            # Merge provider info into canonical record if available
            if provider and provider not in canonical.get("providers", []):
                canonical.setdefault("providers", []).append(provider)

            logger.info(f"Duplicate Model found by HuggingFace ID: '{clean_hf}'")
            return record, True

        # 3. Normalized Repository URL Match
        if norm_url and norm_url in self._repo_url_map:
            canonical_id = self._repo_url_map[norm_url]
            canonical = self._seen_ids[canonical_id]
            record["duplicate_of"] = canonical_id
            record["match_method"] = "exact_repository_url"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate Model found by repository URL: '{norm_url}'")
            return record, True

        # 4. Provider & Name Key Match
        if name_key and name_key in self._canonical_name_map:
            canonical_id = self._canonical_name_map[name_key]
            canonical = self._seen_ids[canonical_id]
            record["duplicate_of"] = canonical_id
            record["match_method"] = "canonical_name_identity_match"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate Model found by provider/name pair: '{name_key}'")
            return record, True

        # Register as new canonical entity
        self._seen_ids[rec_id] = record
        if clean_hf:
            self._hf_id_map[clean_hf] = rec_id
        if norm_url:
            self._repo_url_map[norm_url] = rec_id
        if name_key:
            self._canonical_name_map[name_key] = rec_id

        record["duplicate_of"] = None
        record["match_method"] = None
        record["match_confidence"] = None
        record["is_baseline_match"] = False
        return record, False
