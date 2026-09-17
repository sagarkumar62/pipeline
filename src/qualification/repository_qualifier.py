import re
from typing import Dict, Any, Tuple
from src.utils.logging import setup_logger

logger = setup_logger("repository_qualifier")


class RepositoryQualifier:
    """
    Deterministic qualification engine for Repository entities.
    Enforces explicit precedence: HARD_EXCLUSION > REVIEW_REQUIRED > QUALIFIED.
    
    Hard exclusions filter out non-software repository noise (awesome lists, tutorials,
    courses, cheat sheets, documentation-only collections). Positive signals NEVER override
    a hard exclusion.
    """

    # Hard exclusion keywords (case-insensitive substring or regex)
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
        r"\bbook\b",
        r"\bdocumentation[-_\s]?only\b"
    ]

    def __init__(self, require_active: bool = True, min_stars: int = 10):
        self.require_active = require_active
        self.min_stars = min_stars

    def qualify(self, repo: Dict[str, Any]) -> Tuple[str, str]:
        """
        Qualifies a candidate repository dictionary or RepositoryRecord.
        
        Returns:
            Tuple[status, reason]:
            - ("QUALIFIED", reason)
            - ("HARD_EXCLUSION", reason)
            - ("REVIEW_REQUIRED", reason)
        """
        name = (repo.get("name") or "").lower()
        description = (repo.get("description") or "").lower()
        topics = [t.lower() for t in (repo.get("topics") or [])]
        archived = bool(repo.get("archived", False))
        is_fork = bool(repo.get("fork", False))
        stars = int(repo.get("stars") or repo.get("stargazers_count") or 0)

        combined_text = f"{name} {description} {' '.join(topics)}"

        # -------------------------------------------------------------
        # STAGE 1: HARD EXCLUSIONS (Precedence 1 - Non-negotiable)
        # -------------------------------------------------------------
        # 1.1 Archived check
        if self.require_active and archived:
            return "HARD_EXCLUSION", "Repository is archived"

        # 1.2 Keyword exclusions (tutorials, courses, awesome lists, cheat sheets)
        for kw in self.HARD_EXCLUSION_KEYWORDS:
            if re.search(kw, combined_text, re.IGNORECASE):
                return "HARD_EXCLUSION", f"Matched hard negative pattern '{kw}' (Awesome/Tutorial/Course/CheatSheet)"

        # 1.3 Specific title/name prefix patterns
        if name.startswith("awesome-") or name.startswith("awesome_") or name == "awesome":
            return "HARD_EXCLUSION", "Repository is an awesome list"
        if "100-days-of" in name or "learn-python" in name or "interview" in name:
            return "HARD_EXCLUSION", "Repository is a course/learning path"

        # -------------------------------------------------------------
        # STAGE 2: REVIEW REQUIRED (Precedence 2 - Ambiguous cases)
        # -------------------------------------------------------------
        # 2.1 Forked repository requiring provenance verification
        if is_fork:
            return "REVIEW_REQUIRED", "Repository is a fork; requires owner/upstream verification"

        # 2.2 Missing description and zero topics
        if not description and not topics:
            return "REVIEW_REQUIRED", "Repository lacks description and metadata topics"

        # 2.3 Low star count threshold
        if stars < self.min_stars:
            return "REVIEW_REQUIRED", f"Star count ({stars}) below minimum threshold ({self.min_stars})"

        # -------------------------------------------------------------
        # STAGE 3: QUALIFIED (Precedence 3 - Clean software entity)
        # -------------------------------------------------------------
        return "QUALIFIED", "Repository passed deterministic AI/software qualification criteria"
