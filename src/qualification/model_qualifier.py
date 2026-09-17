import re
from typing import Dict, Any, Tuple
from src.utils.logging import setup_logger

logger = setup_logger("model_qualifier")


class ModelQualifier:
    """
    Deterministic qualification engine for Model entities.
    Enforces strict precedence: HARD_EXCLUSION > REVIEW_REQUIRED > QUALIFIED.
    
    Hard exclusions filter out non-model noise (model comparison articles, benchmark leaderboards/datasets,
    model wrappers, API clients, prompt libraries, tutorials, awesome lists).
    Positive signals NEVER override a hard exclusion.
    """

    HARD_EXCLUSION_KEYWORDS = [
        r"\bawesome[-_\s]",
        r"^awesome-",
        r"\btutorials?\b",
        r"\bcourses?\b",
        r"\bcheat[-_\s]?sheets?\b",
        r"\binterview[-_\s]?prep\b",
        r"\blearn[-_\s]?\b",
        r"\broadmap\b",
        r"\breading[-_\s]?list\b",
        r"\bcurated[-_\s]?list\b",
        r"\bawesome-llm",
        r"\bawesome-models",
        r"\bdocumentation[-_\s]?only\b",
        r"\bblog[-_\s]?post\b",
        r"\bvideo[-_\s]?tutorial\b",
        r"\bbenchmark[-_\s]?leaderboard\b",
        r"\bmodel[-_\s]?comparison\b",
        r"\bmodel[-_\s]?eval\b",
        r"\bevaluation[-_\s]?suite\b",
        r"\bapi[-_\s]?wrapper\b",
        r"\bclient[-_\s]?sdk\b",
        r"\bui[-_\s]?client\b",
        r"\bwrapper[-_\s]?only\b"
    ]

    NON_MODEL_PATTERNS = [
        r"\bllm[-_\s]?wrapper\b",
        r"\bprompt[-_\s]?library\b",
        r"\bprompt[-_\s]?collection\b",
        r"\bbenchmark[-_\s]?dataset\b",
        r"\bleaderboard[-_\s]?only\b",
        r"\bmodel[-_\s]?directory[-_\s]?only\b",
        r"\bchatbot[s]?\b",
        r"\bchat[-_\s]?ui\b",
        r"\bweb[-_\s]?ui\b",
        r"\buser[-_\s]?interface\b"
    ]

    MODEL_POSITIVE_SIGNALS = [
        r"\bllama\b",
        r"\bgpt\b",
        r"\bclaude\b",
        r"\bmistral\b",
        r"\bqwen\b",
        r"\bdeepseek\b",
        r"\bgemini\b",
        r"\bphi[-_\s]?",
        r"\bgemma\b",
        r"\bcommand\b",
        r"\bstable[-_\s]?diffusion\b",
        r"\bflux\b",
        r"\bwhisper\b",
        r"\bembedding[s]?\b",
        r"\bfoundation[-_\s]?model\b",
        r"\blarge[-_\s]?language[-_\s]?model\b",
        r"\bvision[-_\s]?language[-_\s]?model\b",
        r"\bmultimodal[-_\s]?model\b",
        r"\breasoning[-_\s]?model\b"
    ]

    def qualify(self, candidate: Dict[str, Any]) -> Tuple[str, str]:
        """
        Qualifies a candidate Model dictionary or ModelRecord.
        
        Returns:
            Tuple[status, reason]:
            - ("QUALIFIED", reason)
            - ("HARD_EXCLUSION", reason)
            - ("REVIEW_REQUIRED", reason)
        """
        name = (candidate.get("name") or candidate.get("model_name") or "").lower()
        description = (candidate.get("description") or "").lower()
        hf_id = (candidate.get("huggingface_id") or "").lower()
        topics = [t.lower() for t in (candidate.get("topics") or candidate.get("categories") or [])]
        archived = bool(candidate.get("archived", False))

        combined_text = f"{name} {description} {hf_id} {' '.join(topics)}"

        # -------------------------------------------------------------
        # STAGE 1: HARD EXCLUSIONS (Precedence 1 - Non-negotiable)
        # -------------------------------------------------------------
        if archived:
            return "HARD_EXCLUSION", "Repository is archived"

        for kw in self.HARD_EXCLUSION_KEYWORDS:
            if re.search(kw, combined_text, re.IGNORECASE):
                return "HARD_EXCLUSION", f"Matched hard negative pattern '{kw}' (Awesome list / Benchmark leaderboard / Wrapper / Client SDK)"

        for nmp in self.NON_MODEL_PATTERNS:
            if re.search(nmp, combined_text, re.IGNORECASE):
                return "HARD_EXCLUSION", f"Matched non-model pattern '{nmp}' (API wrapper / Benchmark dataset)"

        if name.startswith("awesome-") or "awesome-llm" in name or "awesome-models" in name:
            return "HARD_EXCLUSION", "Repository is a curated awesome list rather than an AI Model entity"

        # -------------------------------------------------------------
        # STAGE 2: POSITIVE EVIDENCE CHECK & REVIEW REQUIRED
        # -------------------------------------------------------------
        has_model_signal = False
        if hf_id:
            has_model_signal = True

        for sig in self.MODEL_POSITIVE_SIGNALS:
            if re.search(sig, combined_text, re.IGNORECASE):
                has_model_signal = True
                break

        model_topics = {"llm", "foundation-model", "ai-model", "vision-language-model", "machine-learning", "deep-learning", "language-model"}
        if any(t in model_topics for t in topics):
            has_model_signal = True

        if not has_model_signal:
            return "HARD_EXCLUSION", "Candidate lacks explicit AI Model / foundation model evidence"

        # -------------------------------------------------------------
        # STAGE 3: REVIEW REQUIRED (Precedence 2 - Ambiguous cases)
        # -------------------------------------------------------------
        if candidate.get("fork", False):
            return "REVIEW_REQUIRED", "Candidate is a fork of a Model repository; requires upstream verification"

        # If model identity or version is ambiguous
        if not description and not hf_id and not candidate.get("context_window"):
            return "REVIEW_REQUIRED", "Candidate lacks description or model card metadata"

        # -------------------------------------------------------------
        # STAGE 4: QUALIFIED (Precedence 3 - Clean Model entity)
        # -------------------------------------------------------------
        return "QUALIFIED", "Candidate verified with concrete AI Model identity evidence"
