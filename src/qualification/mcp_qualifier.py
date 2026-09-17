import re
from typing import Dict, Any, Tuple
from src.utils.logging import setup_logger

logger = setup_logger("mcp_qualifier")


class MCPQualifier:
    """
    Deterministic qualification engine for Model Context Protocol (MCP) entities.
    Enforces explicit precedence: HARD_EXCLUSION > REVIEW_REQUIRED > QUALIFIED.
    
    Hard exclusions filter out non-MCP noise (ordinary AI tools, generic APIs, tutorials,
    awesome lists, blog posts, videos). Positive signals NEVER override a hard exclusion.
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
        r"\bawesome-mcp-list\b",
        r"\bawesome-mcp-servers\b",  # The curated list repository itself
        r"\bdocumentation[-_\s]?only\b",
        r"\bblog[-_\s]?post\b",
        r"\bvideo[-_\s]?tutorial\b"
    ]

    MCP_POSITIVE_SIGNALS = [
        r"\bmcp[-_\s]?server\b",
        r"\bmcp[-_\s]?protocol\b",
        r"\bmodel[-_\s]?context[-_\s]?protocol\b",
        r"@modelcontextprotocol",
        r"\bmcp[-_\s]?tool\b",
        r"\bmcp[-_\s]?connector\b",
        r"\bmcp[-_\s]?plugin\b",
        r"\bmcp[-_\s]?integration\b",
        r"\bmcp[-_\s]?adapter\b"
    ]

    def qualify(self, candidate: Dict[str, Any]) -> Tuple[str, str]:
        """
        Qualifies a candidate MCP dictionary or MCPRecord.
        
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
                return "HARD_EXCLUSION", f"Matched hard negative pattern '{kw}' (Awesome list / Tutorial / Doc-only)"

        if name.startswith("awesome-mcp") or name == "awesome-mcp-servers":
            return "HARD_EXCLUSION", "Repository is a curated awesome list of MCP servers rather than an MCP server"

        # -------------------------------------------------------------
        # STAGE 2: POSITIVE EVIDENCE CHECK & REVIEW REQUIRED
        # -------------------------------------------------------------
        has_mcp_signal = False
        for sig in self.MCP_POSITIVE_SIGNALS:
            if re.search(sig, combined_text, re.IGNORECASE):
                has_mcp_signal = True
                break

        if "mcp" in topics or "mcp-server" in topics:
            has_mcp_signal = True

        if not has_mcp_signal:
            return "HARD_EXCLUSION", "Candidate lacks explicit Model Context Protocol (MCP) implementation evidence"

        # -------------------------------------------------------------
        # STAGE 3: REVIEW REQUIRED (Precedence 2 - Ambiguous cases)
        # -------------------------------------------------------------
        if not description:
            return "REVIEW_REQUIRED", "Candidate has MCP topic but lacks functional description"

        if candidate.get("fork", False):
            return "REVIEW_REQUIRED", "Candidate is a fork of an MCP repository; requires upstream verification"

        # -------------------------------------------------------------
        # STAGE 4: QUALIFIED (Precedence 3 - Clean MCP entity)
        # -------------------------------------------------------------
        return "QUALIFIED", "Candidate verified with concrete Model Context Protocol (MCP) server/tool evidence"
