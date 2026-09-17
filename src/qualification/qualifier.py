"""
GitHub Repository Qualification Filter (Hardened)

Deterministic qualification layer that distinguishes actual AI Tools from
repositories that should not enter the Tool dataset (awesome lists, tutorials,
datasets, benchmarks, courses, resource collections, pentest templates, etc.).

Precedence Order:
    HARD_NON_TOOL > REVIEW_REQUIRED > QUALIFIED_TOOL

Rule: Positive AI/MCP/Agent topic signals MUST NOT cancel Hard Exclusion Signals.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from src.utils.logging import setup_logger

logger = setup_logger("qualifier")


# --- HARD EXCLUSION SIGNALS ---
# Explicit non-tool patterns that CANNOT be cancelled by positive AI/MCP/agent topic tags

HARD_NEGATIVE_NAME_PATTERNS = [
    re.compile(r"^awesome[\-_]", re.IGNORECASE),
    re.compile(r"[\-_]awesome$", re.IGNORECASE),
    re.compile(r"^list[\-_]of[\-_]", re.IGNORECASE),
    re.compile(r"[\-_]tutorial[s]?$", re.IGNORECASE),
    re.compile(r"^tutorial[s]?[\-_]", re.IGNORECASE),
    re.compile(r"[\-_]course[s]?$", re.IGNORECASE),
    re.compile(r"^course[s]?[\-_]", re.IGNORECASE),
    re.compile(r"[\-_]academy$", re.IGNORECASE),
    re.compile(r"^academy[\-_]", re.IGNORECASE),
    re.compile(r"[\-_]curriculum$", re.IGNORECASE),
    re.compile(r"^curriculum[\-_]", re.IGNORECASE),
    re.compile(r"[\-_]cheatsheet[s]?$", re.IGNORECASE),
    re.compile(r"^cheatsheet[s]?[\-_]", re.IGNORECASE),
    re.compile(r"[\-_]interview[\-_]", re.IGNORECASE),
    re.compile(r"^interview[\-_]", re.IGNORECASE),
    re.compile(r"[\-_]dataset[s]?$", re.IGNORECASE),
    re.compile(r"^dataset[s]?[\-_]", re.IGNORECASE),
    re.compile(r"[\-_]benchmark[s]?$", re.IGNORECASE),
    re.compile(r"^benchmark[s]?[\-_]", re.IGNORECASE),
]

HARD_NEGATIVE_DESC_PATTERNS = [
    re.compile(r"\bawesome\s+list\b", re.IGNORECASE),
    re.compile(r"\bcurated\s+list\b", re.IGNORECASE),
    re.compile(r"\blist\s+of\b", re.IGNORECASE),
    re.compile(r"\bcollection\s+of\b", re.IGNORECASE),
    re.compile(r"\bcurriculum\b", re.IGNORECASE),
    re.compile(r"\bacademy\b", re.IGNORECASE),
    re.compile(r"\bresources?\s+for\b", re.IGNORECASE),
    re.compile(r"\bresource\s+list\b", re.IGNORECASE),
    re.compile(r"\btutorial\s+(?:for|on|to|series|guide)\b", re.IGNORECASE),
    re.compile(r"\bvideo\s+course[s]?\b", re.IGNORECASE),
    re.compile(r"\bcheat\s*sheet\b", re.IGNORECASE),
    re.compile(r"\binterview\s+questions?\b", re.IGNORECASE),
    re.compile(r"\bpapers?\s+(?:collection|list|about|on)\b", re.IGNORECASE),
    re.compile(r"\bpenetration\s+test\s+reports?\b", re.IGNORECASE),
    re.compile(r"\bpentest\s+report[s]?\b", re.IGNORECASE),
    re.compile(r"\bdocumentation\s+only\b", re.IGNORECASE),
]

HARD_NEGATIVE_TOPICS = {
    "awesome-list", "awesome", "awesome-lists",
    "tutorial", "tutorials", "course", "courses", "academy", "curriculum", "learning",
    "dataset", "datasets", "benchmark", "benchmarks",
    "interview", "interview-questions", "interview-preparation",
    "cheatsheet", "cheat-sheet",
    "paper", "papers", "research-paper", "research-papers",
    "collection", "resource-list",
}


# --- SOFT NEGATIVE SIGNALS (for REVIEW_REQUIRED) ---

SOFT_NEGATIVE_NAME_PATTERNS = [
    re.compile(r"[\-_]curated[\-_]", re.IGNORECASE),
    re.compile(r"^curated[\-_]", re.IGNORECASE),
    re.compile(r"[\-_]template[s]?$", re.IGNORECASE),
    re.compile(r"[\-_]boilerplate$", re.IGNORECASE),
    re.compile(r"[\-_]examples$", re.IGNORECASE),
    re.compile(r"[\-_]cookbook$", re.IGNORECASE),
    re.compile(r"[\-_]docs$", re.IGNORECASE),
    re.compile(r"[\-_]documentation$", re.IGNORECASE),
    re.compile(r"[\-_]experiments$", re.IGNORECASE),
]

SOFT_NEGATIVE_TOPICS = {
    "reference", "roadmap", "study-guide", "study-notes", "resources",
    "docs", "documentation", "boilerplate", "template", "templates",
    "dotfiles", "portfolio", "blog", "news", "arxiv"
}

POSITIVE_TOPICS = {
    "tool", "tools", "framework", "library", "sdk", "api", "cli",
    "app", "application", "platform", "saas", "devtool", "devtools",
    "developer-tools", "developer-tool", "productivity",
    "ai-tool", "ai-tools", "llm-tool", "llm-tools",
    "mcp", "mcp-server", "mcp-client",
    "agent", "agents", "ai-agent", "ai-agents",
    "automation", "workflow", "pipeline",
    "code-editor", "ide", "extension", "plugin",
    "web-app", "desktop-app", "mobile-app",
    "chatbot", "bot", "assistant",
    "generator", "converter", "analyzer",
    "server", "inference", "deployment",
}


@dataclass
class QualificationResult:
    """Result of repository qualification analysis."""
    status: str  # QUALIFIED_TOOL | REVIEW_REQUIRED | REJECTED_NON_TOOL
    reasons: List[str] = field(default_factory=list)
    signals: Dict[str, Any] = field(default_factory=dict)


class GitHubRepoQualifier:
    """
    Deterministic repository qualification filter (Hardened).
    
    Uses strict precedence:
    - HARD_NON_TOOL: Hard non-tool patterns (awesome lists, curated collections, courses, etc.)
    - REVIEW_REQUIRED: Soft signals, archived repos, or ambiguous boundary cases
    - QUALIFIED_TOOL: Real tool / product / software utility
    
    Hard non-tool signals CANNOT be overridden by positive topic tags.
    """

    def qualify(self, record: Dict[str, Any]) -> QualificationResult:
        name = (record.get("name") or "").strip()
        description = record.get("description")
        topics = record.get("github_topics") or []
        is_fork = record.get("is_fork", False)
        is_archived = record.get("is_archived", False)
        readme_content = record.get("readme_content") or ""

        hard_reasons: List[str] = []
        soft_reasons: List[str] = []
        positive_reasons: List[str] = []

        # 1. Hard Name Pattern Check
        for pattern in HARD_NEGATIVE_NAME_PATTERNS:
            if pattern.search(name):
                hard_reasons.append(f"Hard negative name pattern: {pattern.pattern}")
                break

        # 2. Hard Description Pattern Check
        if description:
            description_str = str(description).strip()
            for pattern in HARD_NEGATIVE_DESC_PATTERNS:
                if pattern.search(description_str):
                    hard_reasons.append(f"Hard negative description pattern: '{pattern.pattern}'")
                    break
        else:
            soft_reasons.append("Missing repository description")

        # 3. Topic Analysis
        topic_set = set(t.lower() for t in topics)
        hard_topic_matches = topic_set & HARD_NEGATIVE_TOPICS
        soft_topic_matches = topic_set & SOFT_NEGATIVE_TOPICS
        pos_topic_matches = topic_set & POSITIVE_TOPICS

        if hard_topic_matches:
            hard_reasons.append(f"Hard negative topics: {', '.join(sorted(hard_topic_matches))}")
        if soft_topic_matches:
            soft_reasons.append(f"Soft negative topics: {', '.join(sorted(soft_topic_matches))}")
        if pos_topic_matches:
            positive_reasons.append(f"Positive topics: {', '.join(sorted(pos_topic_matches))}")

        # 4. Soft Name Pattern Check
        for pattern in SOFT_NEGATIVE_NAME_PATTERNS:
            if pattern.search(name):
                soft_reasons.append(f"Soft negative name pattern: {pattern.pattern}")
                break

        # 5. Fork / Archived
        if is_fork:
            soft_reasons.append("Repository is a fork")
        if is_archived:
            soft_reasons.append("Repository is archived")

        # 6. README Link-List Check
        if readme_content:
            readme_lower = readme_content[:3000].lower()
            link_count = readme_lower.count("](http")
            text_ratio = len(readme_lower.replace(" ", "").replace("\n", ""))
            if link_count > 30 and text_ratio > 0:
                link_density = link_count / (text_ratio / 100)
                if link_density > 2.0:
                    hard_reasons.append(f"README appears to be a link collection (link_count={link_count})")

        signals: Dict[str, Any] = {
            "name": name,
            "is_fork": is_fork,
            "is_archived": is_archived,
            "topics_count": len(topics),
            "negative_topics": list(hard_topic_matches | soft_topic_matches),
            "positive_topics": list(pos_topic_matches),
            "hard_topics": list(hard_topic_matches),
            "soft_topics": list(soft_topic_matches),
            "hard_signal_count": len(hard_reasons),
            "soft_signal_count": len(soft_reasons),
            "negative_signal_count": len(hard_reasons) + len(soft_reasons),
            "positive_signal_count": len(positive_reasons),
        }

        # --- PRECEDENCE EVALUATION ---

        # Check for explicit boundary review cases
        name_lower = name.lower()
        is_boundary_review = (
            ("curated" in name_lower or "template" in name_lower or "experiment" in name_lower or "paper" in name_lower)
            and bool(pos_topic_matches)
        )

        # Precedence Rule 1: HARD EXCLUSIONS
        if hard_reasons:
            if is_boundary_review:
                result = QualificationResult(
                    status="REVIEW_REQUIRED",
                    reasons=hard_reasons + positive_reasons,
                    signals=signals,
                )
                logger.info(f"[REVIEW_REQUIRED] Boundary case '{name}': {', '.join(hard_reasons)}")
            else:
                result = QualificationResult(
                    status="REJECTED_NON_TOOL",
                    reasons=hard_reasons,
                    signals=signals,
                )
                logger.info(f"[REJECTED_NON_TOOL] '{name}': {', '.join(hard_reasons)}")
            return result

        # Precedence Rule 2: SOFT NEGATIVES / AMBIGUITY / MISSING DESCRIPTION
        has_missing_description = not description
        if soft_reasons:
            if len(soft_reasons) >= 2 or is_archived or is_boundary_review or (has_missing_description and not pos_topic_matches):
                result = QualificationResult(
                    status="REVIEW_REQUIRED",
                    reasons=soft_reasons + positive_reasons,
                    signals=signals,
                )
                logger.info(f"[REVIEW_REQUIRED] '{name}': {', '.join(soft_reasons)}")
                return result

        # Precedence Rule 3: QUALIFIED TOOL
        result = QualificationResult(
            status="QUALIFIED_TOOL",
            reasons=positive_reasons if positive_reasons else ["No disqualifying signals found"],
            signals=signals,
        )
        logger.debug(f"[QUALIFIED_TOOL] '{name}'")
        return result


