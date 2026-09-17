import re
from typing import Dict, Any, Tuple
from src.utils.logging import setup_logger

logger = setup_logger("news_qualifier")


class NewsQualifier:
    """
    Deterministic qualification engine for News entities.
    Enforces strict precedence: HARD_EXCLUSION > REVIEW_REQUIRED > QUALIFIED.
    Positive signals NEVER override a hard exclusion.
    """

    NON_ARTICLE_PATTERNS = [
        r"^https?://[^/]+/search\?",
        r"^https?://[^/]+/category/?$",
        r"^https?://[^/]+/tag/?$",
        r"^https?://[^/]+/privacy-policy",
        r"^https?://[^/]+/terms-of-service",
        r"^https?://[^/]+/contact",
        r"^https?://[^/]+/about-us",
        r"^https?://[^/]+/subscribe",
        r"^https?://[^/]+/login",
        r"^https?://[^/]+/register"
    ]

    SPAM_OR_AD_KEYWORDS = [
        r"\bcasino\b",
        r"\bjackpot\b",
        r"\bbetting\b",
        r"\bporn\b",
        r"\bcrypto\s+airdrop\b",
        r"\bget\s+rich\s+quick\b",
        r"\bessay\s+writing\s+service\b"
    ]

    def qualify(self, candidate: Dict[str, Any]) -> Tuple[str, str]:
        """
        Qualifies a candidate News dictionary.
        Returns Tuple[status, reason]:
        - ("HARD_EXCLUSION", reason)
        - ("REVIEW_REQUIRED", reason)
        - ("QUALIFIED", reason)
        """
        title = (candidate.get("title") or candidate.get("name") or "").strip()
        canonical_url = (candidate.get("canonical_url") or candidate.get("url") or "").strip()
        summary = (candidate.get("summary") or "").strip()
        source_domain = (candidate.get("source_domain") or "").strip()

        combined_text = f"{title} {summary}".lower()

        # -------------------------------------------------------------
        # STAGE 1: HARD EXCLUSIONS (Precedence 1 - Non-negotiable)
        # -------------------------------------------------------------
        if not title or len(title) < 5:
            return "HARD_EXCLUSION", "Title missing or under 5 characters"

        if not canonical_url or not (canonical_url.startswith("http://") or canonical_url.startswith("https://")):
            return "HARD_EXCLUSION", "Invalid or missing canonical URL scheme"

        if not source_domain:
            return "HARD_EXCLUSION", "Missing source publisher domain"

        for nap in self.NON_ARTICLE_PATTERNS:
            if re.search(nap, canonical_url, re.IGNORECASE):
                return "HARD_EXCLUSION", f"URL matched non-article pattern '{nap}' (Category / Index / Policy page)"

        for kw in self.SPAM_OR_AD_KEYWORDS:
            if re.search(kw, combined_text, re.IGNORECASE):
                return "HARD_EXCLUSION", f"Matched spam/ad pattern '{kw}'"

        if title.lower() in ("home", "index", "default", "404 not found", "page not found", "error"):
            return "HARD_EXCLUSION", "Generic non-article page title"

        # -------------------------------------------------------------
        # STAGE 2: REVIEW REQUIRED (Precedence 2)
        # -------------------------------------------------------------
        if len(summary) < 15 and len(title) < 20:
            return "REVIEW_REQUIRED", "Extremely low information content (title < 20 chars and summary < 15 chars)"

        # -------------------------------------------------------------
        # STAGE 3: QUALIFIED (Precedence 3)
        # -------------------------------------------------------------
        return "QUALIFIED", "Valid news headline, canonical URL, and attributable publisher provenance"
