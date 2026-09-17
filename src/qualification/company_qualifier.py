import re
from typing import Dict, Any, Tuple
from src.utils.logging import setup_logger

logger = setup_logger("company_qualifier")


class CompanyQualifier:
    """
    Deterministic qualification engine for Company entities.
    Enforces strict precedence: HARD_EXCLUSION > REVIEW_REQUIRED > QUALIFIED.
    
    Filters out non-company noise (generic IT services, AI news publications, AI blogs, AI newsletters,
    AI job boards, AI directories, individual creator accounts, open-source repos without corporate identity).
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
        r"\bblog[-_\s]?post\b",
        r"\bvideo[-_\s]?tutorial\b",
        r"\bnews[-_\s]?letter\b",
        r"\bnews[-_\s]?publication\b",
        r"\bmagazine\b",
        r"\bjob[-_\s]?board\b",
        r"\bdirectory[-_\s]?only\b",
        r"\bcommunity[-_\s]?forum\b",
        r"\bventure[-_\s]?capital\b",
        r"\bvc[-_\s]?fund\b",
        r"\baccelerator[-_\s]?program\b",
        r"\buniversity[-_\s]?lab\b"
    ]

    NON_COMPANY_PATTERNS = [
        r"\bpersonal[-_\s]?account\b",
        r"\bcasual[-_\s]?project\b",
        r"\bcurated[-_\s]?directory\b",
        r"\bit[-_\s]?consulting\b",
        r"\bgeneric[-_\s]?it\b"
    ]

    COMPANY_POSITIVE_SIGNALS = [
        r"\bai\b",
        r"\bartificial[-_\s]?intelligence\b",
        r"\bmachine[-_\s]?learning\b",
        r"\bdeep[-_\s]?learning\b",
        r"\bllm\b",
        r"\bgenerative[-_\s]?ai\b",
        r"\bautonomous[-_\s]?agent\b",
        r"\brobotics\b",
        r"\bcomputer[-_\s]?vision\b",
        r"\bnlp\b",
        r"\bneural\b",
        r"\blabs?\b",
        r"\btechnologies\b",
        r"\bsystems\b"
    ]

    def qualify(self, candidate: Dict[str, Any]) -> Tuple[str, str]:
        """
        Qualifies a candidate Company dictionary or CompanyRecord.
        
        Returns:
            Tuple[status, reason]:
            - ("QUALIFIED", reason)
            - ("HARD_EXCLUSION", reason)
            - ("REVIEW_REQUIRED", reason)
        """
        name = (candidate.get("name") or candidate.get("company_name") or "").lower()
        description = (candidate.get("description") or "").lower()
        official_url = (candidate.get("official_url") or candidate.get("url") or "").lower()
        github_url = (candidate.get("github_url") or "").lower()
        topics = [t.lower() for t in (candidate.get("topics") or candidate.get("categories") or [])]
        type_str = str(candidate.get("type") or "").lower()

        combined_text = f"{name} {description} {official_url} {github_url} {' '.join(topics)}"

        # -------------------------------------------------------------
        # STAGE 1: HARD EXCLUSIONS (Precedence 1 - Non-negotiable)
        # -------------------------------------------------------------
        for kw in self.HARD_EXCLUSION_KEYWORDS:
            if re.search(kw, combined_text, re.IGNORECASE):
                return "HARD_EXCLUSION", f"Matched hard negative pattern '{kw}' (Awesome list / News / Job board / Directory / VC fund)"

        for ncp in self.NON_COMPANY_PATTERNS:
            if re.search(ncp, combined_text, re.IGNORECASE):
                return "HARD_EXCLUSION", f"Matched non-company pattern '{ncp}' (Personal account / IT consulting)"

        if name.startswith("awesome-") or "awesome-ai" in name or "awesome-companies" in name:
            return "HARD_EXCLUSION", "Repository is a curated list rather than an AI Company"

        if type_str == "user":
            return "HARD_EXCLUSION", "Entity is an individual GitHub user account rather than a corporate organization"

        # -------------------------------------------------------------
        # STAGE 2: POSITIVE EVIDENCE CHECK & REVIEW REQUIRED
        # -------------------------------------------------------------
        has_ai_signal = False
        for sig in self.COMPANY_POSITIVE_SIGNALS:
            if re.search(sig, combined_text, re.IGNORECASE):
                has_ai_signal = True
                break

        if not has_ai_signal:
            return "HARD_EXCLUSION", "Candidate lacks explicit AI centrality or corporate AI business evidence"

        # -------------------------------------------------------------
        # STAGE 3: REVIEW REQUIRED (Precedence 2 - Ambiguous cases)
        # -------------------------------------------------------------
        if candidate.get("review_required") or "unclear" in name:
            return "REVIEW_REQUIRED", "Company identity or corporate status is ambiguous and requires review"

        # -------------------------------------------------------------
        # STAGE 4: QUALIFIED (Precedence 3 - Clean Company entity)
        # -------------------------------------------------------------
        return "QUALIFIED", "Candidate verified with concrete AI Company identity evidence"
