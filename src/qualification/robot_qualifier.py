import re
from typing import Dict, Any, Tuple
from src.utils.logging import setup_logger

logger = setup_logger("robot_qualifier")


class RobotQualifier:
    """
    Deterministic qualification engine for Robot entities.
    Enforces strict precedence: HARD_EXCLUSION > REVIEW_REQUIRED > QUALIFIED.
    
    Filters out software-only bots, chatbots, AI software agents, robotics articles/news,
    courses, simulators without physical robots, SDKs, and awesome lists.
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
        r"\bawesome-robotics",
        r"\bawesome-ros",
        r"\bblog[-_\s]?post\b",
        r"\bvideo[-_\s]?tutorial\b",
        r"\bnews[-_\s]?letter\b",
        r"\bnews[-_\s]?publication\b",
        r"\bmagazine\b",
        r"\bjob[-_\s]?board\b",
        r"\bdirectory[-_\s]?only\b",
        r"\bchatbot[-_\s]?only\b",
        r"\bdiscord[-_\s]?bot\b",
        r"\btelegram[-_\s]?bot\b",
        r"\bslack[-_\s]?bot\b",
        r"\bweb[-_\s]?scraper\b",
        r"\brpa[-_\s]?software\b"
    ]

    NON_ROBOT_PATTERNS = [
        r"\bsoftware[-_\s]?bot\b",
        r"\bbrowser[-_\s]?bot\b",
        r"\btrading[-_\s]?bot\b",
        r"\bcrypto[-_\s]?bot\b",
        r"\bsimulator[-_\s]?only\b",
        r"\bdataset[-_\s]?only\b"
    ]

    ROBOT_POSITIVE_SIGNALS = [
        r"\bhumanoid[s]?\b",
        r"\bquadruped[s]?\b",
        r"\bquadrupedal\b",
        r"\bbiped[s]?\b",
        r"\bbipedal\b",
        r"\barm[s]?\b",
        r"\bmanipulator[s]?\b",
        r"\brobotic[s]?\b",
        r"\brobot[s]?\b",
        r"\bmobile[-_\s]?robot[s]?\b",
        r"\bamr\b",
        r"\bagv\b",
        r"\brover[s]?\b",
        r"\bdrone[s]?\b",
        r"\bexoskeleton[s]?\b",
        r"\bactuator[s]?\b",
        r"\bservo[s]?\b",
        r"\bros\b",
        r"\bros2\b"
    ]

    def qualify(self, candidate: Dict[str, Any]) -> Tuple[str, str]:
        """
        Qualifies a candidate Robot dictionary or RobotRecord.
        
        Returns:
            Tuple[status, reason]:
            - ("QUALIFIED", reason)
            - ("HARD_EXCLUSION", reason)
            - ("REVIEW_REQUIRED", reason)
        """
        name = (candidate.get("name") or "").lower()
        description = (candidate.get("description") or "").lower()
        topics = [t.lower() for t in (candidate.get("topics") or candidate.get("categories") or [])]
        archived = bool(candidate.get("archived", False))

        combined_text = f"{name} {description} {' '.join(topics)}"

        # -------------------------------------------------------------
        # STAGE 1: HARD EXCLUSIONS (Precedence 1 - Non-negotiable)
        # -------------------------------------------------------------
        if archived:
            return "HARD_EXCLUSION", "Repository is archived"

        for kw in self.HARD_EXCLUSION_KEYWORDS:
            if re.search(kw, combined_text, re.IGNORECASE):
                return "HARD_EXCLUSION", f"Matched hard negative pattern '{kw}' (Awesome list / Software bot / Chatbot / News / Course)"

        for nrp in self.NON_ROBOT_PATTERNS:
            if re.search(nrp, combined_text, re.IGNORECASE):
                return "HARD_EXCLUSION", f"Matched non-robot pattern '{nrp}' (Software bot / Trading bot / Scraper)"

        if name.startswith("awesome-") or "awesome-robotics" in name or "awesome-ros" in name:
            return "HARD_EXCLUSION", "Repository is a curated awesome list rather than a physical Robot"

        # -------------------------------------------------------------
        # STAGE 2: POSITIVE EVIDENCE CHECK & REVIEW REQUIRED
        # -------------------------------------------------------------
        has_robot_signal = False
        for sig in self.ROBOT_POSITIVE_SIGNALS:
            if re.search(sig, combined_text, re.IGNORECASE):
                has_robot_signal = True
                break

        robot_topics = {"robotics", "robot", "humanoid-robot", "quadruped", "mobile-robot", "ros-robot", "open-robotics", "ros"}
        if any(t in robot_topics for t in topics):
            has_robot_signal = True

        if not has_robot_signal:
            return "HARD_EXCLUSION", "Candidate lacks explicit physical Robot / robotics hardware implementation evidence"

        # -------------------------------------------------------------
        # STAGE 3: REVIEW REQUIRED (Precedence 2 - Ambiguous cases)
        # -------------------------------------------------------------
        if candidate.get("fork", False):
            return "REVIEW_REQUIRED", "Candidate is a fork of a Robotics repository; requires upstream verification"

        if not description and not candidate.get("official_url"):
            return "REVIEW_REQUIRED", "Robot candidate lacks description and official product landing page"

        # -------------------------------------------------------------
        # STAGE 4: QUALIFIED (Precedence 3 - Clean Robot entity)
        # -------------------------------------------------------------
        return "QUALIFIED", "Candidate verified with concrete physical Robot / robotics hardware evidence"
