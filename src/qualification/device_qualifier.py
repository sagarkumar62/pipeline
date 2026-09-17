import re
from typing import Dict, Any, Tuple
from src.utils.logging import setup_logger

logger = setup_logger("device_qualifier")


class DeviceQualifier:
    """
    Deterministic qualification engine for Device entities.
    Enforces strict precedence: HARD_EXCLUSION > REVIEW_REQUIRED > QUALIFIED.
    
    Filters out software-only packages, APIs/SDKs without hardware, chatbots, AI agents,
    hardware articles/news, courses, awesome lists, and full physical robots (which belong to the Robots module).
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
        r"\bchatbot[-_\s]?only\b",
        r"\bdiscord[-_\s]?bot\b",
        r"\btelegram[-_\s]?bot\b",
        r"\bslack[-_\s]?bot\b",
        r"\bweb[-_\s]?scraper\b",
        r"\brpa[-_\s]?software\b"
    ]

    NON_DEVICE_PATTERNS = [
        r"\bsoftware[-_\s]?only\b",
        r"\bbrowser[-_\s]?extension\b",
        r"\btrading[-_\s]?bot\b",
        r"\bcrypto[-_\s]?bot\b",
        r"\bsimulator[-_\s]?only\b",
        r"\bdataset[-_\s]?only\b",
        r"\bpython[-_\s]?package\b",
        r"\bjavascript[-_\s]?library\b",
        r"\bsdk[s]?\b",
        r"\bpython[-_\s]?sdk\b",
        r"\bsoftware[-_\s]?library\b",
        r"\bmodel[-_\s]?weights\b",
        r"\bsaas\b",
        r"\bdashboard\b"
    ]

    ROBOT_MODULE_PATTERNS = [
        r"\bhumanoid[-_\s]?robot\b",
        r"\bquadruped[-_\s]?robot\b",
        r"\barm[-_\s]?manipulator\b",
        r"\brobotic[-_\s]?arm\b",
        r"\bautonomous[-_\s]?rover\b"
    ]

    DEVICE_POSITIVE_SIGNALS = [
        r"\bedge[-_\s]?ai\b",
        r"\bai[-_\s]?accelerator[s]?\b",
        r"\bai[-_\s]?hardware\b",
        r"\bai[-_\s]?camera[s]?\b",
        r"\bai[-_\s]?wearable[s]?\b",
        r"\bai[-_\s]?device[s]?\b",
        r"\bai[-_\s]?workstation[s]?\b",
        r"\bdev[-_\s]?kit[s]?\b",
        r"\bdevkit[s]?\b",
        r"\bjetson\b",
        r"\bhailo\b",
        r"\bcoral[-_\s]?tpu\b",
        r"\bnpu\b",
        r"\bsingle[-_\s]?board[-_\s]?computer\b",
        r"\bsbc\b",
        r"\bpcb\b",
        r"\bschematics\b"
    ]

    def qualify(self, candidate: Dict[str, Any]) -> Tuple[str, str]:
        """
        Qualifies a candidate Device dictionary or DeviceRecord.
        
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

        for ndp in self.NON_DEVICE_PATTERNS:
            if re.search(ndp, combined_text, re.IGNORECASE):
                return "HARD_EXCLUSION", f"Matched non-device pattern '{ndp}' (Software only / Extension / Library)"

        for rmp in self.ROBOT_MODULE_PATTERNS:
            if re.search(rmp, combined_text, re.IGNORECASE):
                return "HARD_EXCLUSION", f"Matched Robot module pattern '{rmp}'; entity belongs to Robots module"

        if name.startswith("awesome-") or "awesome-ai-hardware" in name:
            return "HARD_EXCLUSION", "Repository is a curated awesome list rather than a physical Device"

        # -------------------------------------------------------------
        # STAGE 2: POSITIVE EVIDENCE CHECK & REVIEW REQUIRED
        # -------------------------------------------------------------
        has_device_signal = False
        for sig in self.DEVICE_POSITIVE_SIGNALS:
            if re.search(sig, combined_text, re.IGNORECASE):
                has_device_signal = True
                break

        device_topics = {"edge-ai", "ai-hardware", "jetson", "npu", "coral-tpu", "hailo", "embedded-ai", "ai-camera"}
        if any(t in device_topics for t in topics):
            has_device_signal = True

        if not has_device_signal:
            return "HARD_EXCLUSION", "Candidate lacks explicit physical AI hardware / Device evidence"

        # -------------------------------------------------------------
        # STAGE 3: REVIEW REQUIRED (Precedence 2 - Ambiguous cases)
        # -------------------------------------------------------------
        if candidate.get("fork", False):
            return "REVIEW_REQUIRED", "Candidate is a fork of a Device repository; requires upstream verification"

        if not description and not candidate.get("official_url"):
            return "REVIEW_REQUIRED", "Device candidate lacks description and official product landing page"

        if any(k in combined_text for k in ["robot", "robotics"]) and not any(k in combined_text for k in ["dev-kit", "board", "chip", "camera", "accelerator"]):
            return "REVIEW_REQUIRED", "Ambiguous classification between Device and Robot modules"

        # -------------------------------------------------------------
        # STAGE 4: QUALIFIED (Precedence 3 - Clean Device entity)
        # -------------------------------------------------------------
        return "QUALIFIED", "Candidate verified with concrete physical AI hardware / Device evidence"
