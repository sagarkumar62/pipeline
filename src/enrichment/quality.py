"""
Phase 4B Description Quality Checker

Detects generic descriptions, marketing hype, tautological definitions, and low-information text.
"""

import re
from typing import Tuple, List, Dict, Any, Optional
from src.utils.logging import setup_logger

logger = setup_logger("description_quality_checker")


class DescriptionQualityChecker:
    """Evaluates generated LLM descriptions for information quality and marketing hype."""

    # Generic & marketing superlatives
    MARKETING_PATTERNS = [
        r'\brevolutionary\b', r'\bgame-changing\b', r'\bworld[\'-]?s\s+best\b',
        r'\bcutting-edge\b', r'\bstate-of-the-art\b', r'\bnext-generation\b',
        r'\bunparalleled\b', r'\bgroundbreaking\b', r'\bmarket-leading\b'
    ]

    # Generic / low-information phrases
    GENERIC_PATTERNS = [
        r'\ban?\s+innovative\s+ai\s+tool\b',
        r'\ba\s+powerful\s+ai\s+platform\b',
        r'\bhelps\s+users\s+achieve\s+their\s+goals\b',
        r'\bboosts?\s+productivity\s+and\s+efficiency\b',
        r'\bdesigned\s+to\s+make\s+your\s+life\s+easier\b'
    ]

    # Tautological phrases
    TAUTOLOGICAL_PATTERNS = [
        r'\ba\s+tool\s+that\s+helps\s+users\s+use\s+ai\b',
        r'\ban?\s+ai\s+tool\s+for\s+ai\b',
        r'\ba\s+software\s+tool\s+that\s+is\s+a\s+tool\b'
    ]

    def check_quality(self, description: str, tool_name: str) -> Tuple[str, bool]:
        """
        Evaluates a description string.
        Returns (quality_flag, is_quality_pass).
        Flags: VALID, MARKETING_LANGUAGE, GENERIC, TAUTOLOGICAL, LOW_INFORMATION
        """
        if not description or not description.strip():
            return "LOW_INFORMATION", False

        desc = description.strip()
        desc_lower = desc.lower()

        # Check tautological
        for pat in self.TAUTOLOGICAL_PATTERNS:
            if re.search(pat, desc_lower):
                return "TAUTOLOGICAL", False

        # Check marketing language
        for pat in self.MARKETING_PATTERNS:
            if re.search(pat, desc_lower):
                return "MARKETING_LANGUAGE", False

        # Check generic phrases
        for pat in self.GENERIC_PATTERNS:
            if re.search(pat, desc_lower):
                return "GENERIC", False

        # Check low information (extremely short or slogan-like)
        if len(desc) < 30 or desc_lower.startswith("runs anywhere"):
            return "LOW_INFORMATION", False

        return "VALID", True
