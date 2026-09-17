"""
Phase 4 Grounding Validator

Validates structured LLM outputs against the supplied EvidencePackage to ensure zero hallucinations,
strict source URL citation matching, and absence of unsupported claims.
"""

import re
from typing import Tuple, List, Dict, Any, Optional
from src.enrichment.schema import EvidencePackage, StructuredLLMOutput
from src.utils.logging import setup_logger

logger = setup_logger("grounding_validator")


class GroundingValidator:
    """Validates LLM-generated descriptions for strict grounding against evidence packages."""

    # Unsupported claim patterns (if not explicitly present in evidence package)
    UNSUPPORTED_PRICING_PATTERNS = [
        r'\$\d+', r'\b\d+\s*dollars\b', r'\bper\s+month\b', r'\bmonthly\s+subscription\b', r'\bpricing\s+tier\b'
    ]
    UNSUPPORTED_METRIC_PATTERNS = [
        r'\b\d+[\d,]*\s*users\b', r'\b\d+[\d,]*\s*customers\b', r'\b\d+[\d,]*\s*downloads\b'
    ]
    UNSUPPORTED_COMPANY_PATTERNS = [
        r'\bfounded\s+in\s+\d{4}\b', r'\bheadquartered\s+in\b'
    ]

    def validate(self, llm_output: StructuredLLMOutput, evidence: EvidencePackage) -> Tuple[bool, str]:
        """
        Validates a StructuredLLMOutput against the supplied EvidencePackage.
        Returns (is_grounded: bool, reason: str).
        """
        if not llm_output or not llm_output.description:
            return False, "EMPTY_DESCRIPTION"

        desc = llm_output.description.strip()
        if len(desc) < 15:
            return False, "DESCRIPTION_TOO_SHORT"

        if len(desc) > 350:
            return False, "DESCRIPTION_EXCEEDS_LENGTH_LIMIT"

        # Sentence count validation (max 2 sentences)
        sentences = [s.strip() for s in re.split(r'[.!?]+', desc) if s.strip()]
        if len(sentences) > 3:  # Allowing up to 2-3 short clauses, reject >= 4
            return False, "DESCRIPTION_EXCEEDS_SENTENCE_LIMIT"

        if not llm_output.grounded:
            return False, "MODEL_UNGROUNDED_FLAG"

        # Validate cited evidence URLs belong to supplied evidence package
        valid_source_urls = set(evidence.source_urls)
        for ev in llm_output.evidence_used:
            if ev.source_url and ev.source_url not in valid_source_urls:
                return False, f"UNCITED_SOURCE_URL: {ev.source_url} not in evidence package"

        # Check for unsupported claims against evidence text
        full_evidence_text = (
            f"{evidence.tool_name} {evidence.repository_description or ''} "
            f"{evidence.readme_excerpt or ''} {evidence.official_website_content or ''} "
            f"{' '.join(evidence.topics)} {evidence.company_name or ''}"
        ).lower()

        # 1. Pricing claim check
        for pat in self.UNSUPPORTED_PRICING_PATTERNS:
            if re.search(pat, desc.lower()) and not re.search(pat, full_evidence_text):
                return False, f"UNSUPPORTED_PRICING_CLAIM: Matched '{pat}'"

        # 2. Metric claim check
        for pat in self.UNSUPPORTED_METRIC_PATTERNS:
            if re.search(pat, desc.lower()) and not re.search(pat, full_evidence_text):
                return False, f"UNSUPPORTED_METRIC_CLAIM: Matched '{pat}'"

        # 3. Company/Founder claim check
        for pat in self.UNSUPPORTED_COMPANY_PATTERNS:
            if re.search(pat, desc.lower()) and not re.search(pat, full_evidence_text):
                return False, f"UNSUPPORTED_COMPANY_CLAIM: Matched '{pat}'"

        return True, "VALID_GROUNDED"
