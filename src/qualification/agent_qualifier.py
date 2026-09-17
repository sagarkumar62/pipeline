import re
from typing import Dict, Any, Tuple
from src.utils.logging import setup_logger

logger = setup_logger("agent_qualifier")


class AgentQualifier:
    """
    Deterministic qualification engine for Agent entities.
    Enforces strict precedence: HARD_EXCLUSION > REVIEW_REQUIRED > QUALIFIED.
    
    Hard exclusions filter out non-agent noise (ordinary AI tools, basic chatbots, generic LLM wrappers,
    prompt libraries, tutorials, awesome lists, blog posts, benchmarks).
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
        r"\bawesome-agent",
        r"\bawesome-ai-agents",
        r"\bawesome-agentic",
        r"\bdocumentation[-_\s]?only\b",
        r"\bblog[-_\s]?post\b",
        r"\bvideo[-_\s]?tutorial\b",
        r"\bbenchmark[s]?\b",
        r"\bdatasets?\b",
        r"\bprompt[-_\s]?library\b",
        r"\bprompt[-_\s]?generator\b",
        r"\bprompt[-_\s]?engineering\b",
        r"\bchatbot[-_\s]?only\b",
        r"\bwrapper[-_\s]?only\b"
    ]

    NON_AGENT_PATTERNS = [
        r"\bsimple[-_\s]?chatbot\b",
        r"\bbasic[-_\s]?chatbot\b",
        r"\bllm[-_\s]?wrapper\b",
        r"\bapi[-_\s]?wrapper\b",
        r"\bprompt[-_\s]?collection\b",
        r"\bstatic[-_\s]?rag\b"
    ]

    AGENT_POSITIVE_SIGNALS = [
        r"\bai[-_\s]?agent[s]?\b",
        r"\bautonomous[-_\s]?agent[s]?\b",
        r"\bagent[-_\s]?framework\b",
        r"\bagent[-_\s]?sdk\b",
        r"\bagent[-_\s]?platform\b",
        r"\bagent[-_\s]?runtime\b",
        r"\bagent[-_\s]?orchestration\b",
        r"\bagent[-_\s]?loop\b",
        r"\bcoding[-_\s]?agent\b",
        r"\bbrowser[-_\s]?agent\b",
        r"\bresearch[-_\s]?agent\b",
        r"\bmulti[-_\s]?agent\b",
        r"\bagentic[-_\s]?ai\b",
        r"\btool[-_\s]?using[-_\s]?agent\b",
        r"\bplanning[-_\s]?agent\b",
        r"\breact[-_\s]?agent\b",
        r"\bswe[-_\s]?bench\b",
        r"\bauto[-_\s]?gpt\b",
        r"\bcrewai\b",
        r"\bautogen\b",
        r"\blanggraph\b"
    ]

    def qualify(self, candidate: Dict[str, Any]) -> Tuple[str, str]:
        """
        Qualifies a candidate Agent dictionary or AgentRecord.
        
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
                return "HARD_EXCLUSION", f"Matched hard negative pattern '{kw}' (Awesome list / Tutorial / Benchmark / Prompt library)"

        for nap in self.NON_AGENT_PATTERNS:
            if re.search(nap, combined_text, re.IGNORECASE):
                return "HARD_EXCLUSION", f"Matched non-agent pattern '{nap}' (Ordinary chatbot / Generic LLM wrapper)"

        if name.startswith("awesome-") or "awesome-agent" in name:
            return "HARD_EXCLUSION", "Repository is a curated list rather than an Agent"

        # -------------------------------------------------------------
        # STAGE 2: POSITIVE EVIDENCE CHECK & REVIEW REQUIRED
        # -------------------------------------------------------------
        has_agent_signal = False
        for sig in self.AGENT_POSITIVE_SIGNALS:
            if re.search(sig, combined_text, re.IGNORECASE):
                has_agent_signal = True
                break

        agent_topics = {"ai-agent", "ai-agents", "autonomous-agent", "agent-framework", "coding-agent", "browser-agent", "multi-agent", "agentic-ai", "agent"}
        if any(t in agent_topics for t in topics):
            has_agent_signal = True

        if not has_agent_signal:
            return "HARD_EXCLUSION", "Candidate lacks explicit AI Agent / agentic functionality evidence"

        # -------------------------------------------------------------
        # STAGE 3: REVIEW REQUIRED (Precedence 2 - Ambiguous cases)
        # -------------------------------------------------------------
        if not description:
            return "REVIEW_REQUIRED", "Candidate has Agent topic but lacks functional description"

        if candidate.get("fork", False):
            return "REVIEW_REQUIRED", "Candidate is a fork of an Agent repository; requires upstream verification"

        # If description mentions "agent" only incidentally or ambivalently
        if len(description) < 20 and not any(k in description for k in ["agent", "autonomous", "framework"]):
            return "REVIEW_REQUIRED", "Ambiguous agent description requires manual review"

        # -------------------------------------------------------------
        # STAGE 4: QUALIFIED (Precedence 3 - Clean Agent entity)
        # -------------------------------------------------------------
        return "QUALIFIED", "Candidate verified with concrete AI Agent / agentic evidence"
