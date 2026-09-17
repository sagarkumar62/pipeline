from typing import Dict, Any
from src.extraction.base import BaseExtractor
from src.models.agent import AgentRecord
from src.models.base import DiscoverySource, EvidenceSource


class AgentExtractor(BaseExtractor):
    """
    Extractor for Agent entities from GitHub Agent Search and discovery sources.
    Extracts structured Agent metadata fields while preserving provenance.
    """

    def extract(self, raw_item: Dict[str, Any], source_name: str = "GitHub Agent Search") -> Dict[str, Any]:
        owner_info = raw_item.get("owner")
        if isinstance(owner_info, dict):
            owner = owner_info.get("login", "")
        else:
            owner = str(owner_info or "").strip()

        name = (raw_item.get("name") or "").strip()
        html_url = raw_item.get("html_url") or raw_item.get("url") or f"https://github.com/{owner}/{name}"

        license_info = raw_item.get("license")
        license_spdx = None
        if isinstance(license_info, dict):
            license_spdx = license_info.get("spdx_id") or license_info.get("name")
        elif isinstance(license_info, str):
            license_spdx = license_info

        query = raw_item.get("_discovery_query") or "topic:ai-agent"
        src_name = raw_item.get("_discovery_source") or source_name

        topics = [t.lower() for t in (raw_item.get("topics") or [])]
        desc = (raw_item.get("description") or "").lower()
        name_lower = name.lower()
        combined_text = f"{name_lower} {desc} {' '.join(topics)}"

        # Determine agent type based on explicit evidence
        agent_type = "AI Agent"
        if any(k in combined_text for k in ["framework", "agent-framework", "sdk", "runtime", "orchestration"]):
            agent_type = "Agent Framework"
        elif any(k in combined_text for k in ["platform", "cloud", "e2b", "modal"]):
            agent_type = "Agent Platform"
        elif any(k in combined_text for k in ["coding", "code", "swe", "developer", "copilot"]):
            agent_type = "Coding Agent"
        elif any(k in combined_text for k in ["browser", "web-agent", "selenium", "playwright"]):
            agent_type = "Browser Agent"
        elif any(k in combined_text for k in ["research", "paper", "search", "rag"]):
            agent_type = "Research Agent"
        elif any(k in combined_text for k in ["multi-agent", "autogen", "crewai"]):
            agent_type = "Multi-Agent System"
        elif any(k in combined_text for k in ["autonomous", "auto-gpt"]):
            agent_type = "Autonomous Agent"

        # Determine underlying framework if explicitly mentioned
        agent_framework = None
        if "langchain" in combined_text or "langgraph" in combined_text:
            agent_framework = "LangChain"
        elif "autogen" in combined_text:
            agent_framework = "AutoGen"
        elif "crewai" in combined_text:
            agent_framework = "CrewAI"
        elif "llamaindex" in combined_text:
            agent_framework = "LlamaIndex"

        # Capabilities derived strictly from evidence
        capabilities = []
        if any(k in combined_text for k in ["tool", "tools", "function-calling", "action"]):
            capabilities.append("tool_use")
        if any(k in combined_text for k in ["plan", "planning", "react", "tree-of-thoughts"]):
            capabilities.append("planning")
        if any(k in combined_text for k in ["memory", "vector", "episodic", "state"]):
            capabilities.append("memory")
        if any(k in combined_text for k in ["multi-step", "workflow", "loop", "autonomous"]):
            capabilities.append("multi_step")
        if any(k in combined_text for k in ["browser", "playwright", "puppeteer"]):
            capabilities.append("browser_automation")

        # Tools used derived from evidence
        tools_used = []
        if "search" in combined_text or "google" in combined_text or "tavily" in combined_text:
            tools_used.append("WebSearch")
        if "code" in combined_text or "python" in combined_text or "interpreter" in combined_text:
            tools_used.append("CodeInterpreter")
        if "file" in combined_text or "filesystem" in combined_text:
            tools_used.append("FileSystem")
        if "browser" in combined_text:
            tools_used.append("Browser")

        # Memory mechanism
        memory = None
        if "vector" in combined_text or "chroma" in combined_text or "pinecone" in combined_text:
            memory = "Vector DB"
        elif "episodic" in combined_text:
            memory = "Episodic"
        elif "memory" in combined_text:
            memory = "Conversation Buffer"

        # Planning paradigm
        planning = None
        if "react" in combined_text:
            planning = "ReAct"
        elif "plan-and-execute" in combined_text or "plan" in combined_text:
            planning = "Plan-and-Execute"

        discovery_src = DiscoverySource(
            name=src_name,
            url=f"https://api.github.com/search/repositories?q={query}",
            source_type="API",
            source_trust_level="HIGH"
        )

        evidence_src = EvidenceSource(
            url=html_url,
            source_type="GITHUB_REPOSITORY",
            trust_level="HIGH",
            evidence_type="CODE_REPOSITORY"
        )

        extracted = {
            "name": name,
            "maintainer": owner,
            "url": html_url,
            "repository_url": html_url,
            "official_url": raw_item.get("homepage"),
            "description": raw_item.get("description"),
            "categories": ["Agent", "Artificial Intelligence"],
            "language": raw_item.get("language"),
            "license": license_spdx,
            "agent_type": agent_type,
            "agent_framework": agent_framework,
            "capabilities": capabilities,
            "tools_used": tools_used,
            "memory": memory,
            "planning": planning,
            "tool_use": "tool_use" in capabilities,
            "open_source": not raw_item.get("private", False),
            "discovery_source": discovery_src,
            "source": discovery_src,
            "evidence_sources": [evidence_src]
        }
        return extracted

    def to_record(self, raw_item: Dict[str, Any], source_name: str = "GitHub Agent Search") -> AgentRecord:
        extracted = self.extract(raw_item, source_name)
        return AgentRecord.create_canonical(**extracted)
