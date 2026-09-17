from typing import Dict, List, Any
import yaml
from pathlib import Path
from src.utils.logging import setup_logger

logger = setup_logger("classifier")


# Topic-to-category mapping for GitHub repositories
# Maps lowercase GitHub topics to taxonomy categories
TOPIC_CATEGORY_MAP = {
    # MCP
    "mcp": "MCP", "mcp-server": "MCP", "mcp-client": "MCP",
    "model-context-protocol": "MCP",
    # Agents
    "agent": "Agents", "agents": "Agents", "ai-agent": "Agents",
    "ai-agents": "Agents", "llm-agent": "Agents", "multi-agent": "Agents",
    "autonomous-agent": "Agents", "agentic": "Agents",
    # Models
    "llm": "Models", "language-model": "Models", "foundation-model": "Models",
    "model": "Models", "transformer": "Models", "fine-tuning": "Models",
    "gguf": "Models", "onnx": "Models", "model-serving": "Models",
    # Image Generation
    "text-to-image": "Image Generation", "image-generation": "Image Generation",
    "stable-diffusion": "Image Generation", "diffusion": "Image Generation",
    "midjourney": "Image Generation", "dalle": "Image Generation",
    "image-synthesis": "Image Generation", "generative-art": "Image Generation",
    # Video
    "video-generation": "Video", "text-to-video": "Video",
    "video-editing": "Video", "video-ai": "Video",
    # Audio
    "text-to-speech": "Audio", "tts": "Audio", "speech-to-text": "Audio",
    "stt": "Audio", "voice": "Audio", "audio": "Audio",
    "music-generation": "Audio", "voice-cloning": "Audio", "asr": "Audio",
    # Coding
    "code-generation": "Coding", "code-completion": "Coding",
    "coding-assistant": "Coding", "ide": "Coding", "code-editor": "Coding",
    "pair-programming": "Coding", "copilot": "Coding",
    # Writing
    "writing": "Writing", "text-generation": "Writing",
    "copywriting": "Writing", "content-generation": "Writing",
    "grammar": "Writing", "translation": "Writing",
    # Automation
    "automation": "Automation", "workflow": "Automation",
    "workflow-automation": "Automation", "no-code": "Automation",
    "low-code": "Automation", "rpa": "Automation",
    # Productivity
    "productivity": "Productivity", "note-taking": "Productivity",
    "task-management": "Productivity", "calendar": "Productivity",
    "knowledge-management": "Productivity",
    # Research
    "research": "Research", "paper": "Research",
    "scientific": "Research", "academic": "Research",
    "literature-review": "Research", "citation": "Research",
    # Design
    "design": "Design", "ui-design": "Design", "ux": "Design",
    "3d": "Design", "3d-generation": "Design", "cad": "Design",
    # Marketing
    "marketing": "Marketing", "seo": "Marketing",
    "social-media": "Marketing", "advertising": "Marketing",
    # Data Analysis
    "data-analysis": "Data Analysis", "analytics": "Data Analysis",
    "visualization": "Data Analysis", "business-intelligence": "Data Analysis",
    # AI Assistants
    "chatbot": "AI Assistants", "chat": "AI Assistants",
    "conversational-ai": "AI Assistants", "assistant": "AI Assistants",
    "virtual-assistant": "AI Assistants",
    # Creative
    "creative": "Creative", "art": "Creative",
    "creative-coding": "Creative", "generative": "Creative",
    # Developer Tools (broad fallback)
    "developer-tools": "Developer Tools", "devtools": "Developer Tools",
    "devtool": "Developer Tools", "developer-tool": "Developer Tools",
    "api": "Developer Tools", "sdk": "Developer Tools",
    "framework": "Developer Tools", "library": "Developer Tools",
    "cli": "Developer Tools", "tool": "Developer Tools",
    "vector-database": "Developer Tools", "rag": "Developer Tools",
    "retrieval-augmented-generation": "Developer Tools",
    "embedding": "Developer Tools", "inference": "Developer Tools",
    "mlops": "Developer Tools", "observability": "Developer Tools",
}

# Description keyword patterns for category inference (applied when topics are insufficient or to refine categories)
DESC_CATEGORY_PATTERNS = [
    # Order matters — more specific patterns first
    (["mcp server", "mcp client", "model context protocol"], "MCP"),
    (["ai agent", "multi-agent", "autonomous agent", "agentic", "agents that use", "agent framework"], "Agents"),
    (["image generation", "text-to-image", "diffusion model", "stable diffusion", "generative art"], "Image Generation"),
    (["video generation", "text-to-video", "video editing", "video ai"], "Video"),
    (["text-to-speech", "speech-to-text", "voice cloning", "music generation", "audio generation", "tts ", " asr"], "Audio"),
    (["code execution", "code runner", "code completion", "code generation", "pair programming", "coding assistant", " ide ", "code editor"], "Coding"),
    (["prompt optimizer", "prompt optimization", "prompt engineering", "prompt library"], "Productivity"),
    (["writing assistant", "grammar", "copywriting", "content generation", "translation"], "Writing"),
    (["workflow automation", "automation platform", "browser automation", " rpa ", "no-code", "low-code"], "Automation"),
    (["productivity", "note-taking", "task management", "knowledge management"], "Productivity"),
    (["research assistant", "literature review", "paper search", "academic research", "ml research"], "Research"),
    (["3d generation", "ui design", "design tool", "3d model"], "Design"),
    (["marketing", " seo ", "social media", "ad copy"], "Marketing"),
    (["data analysis", "visualization", "dashboard", "business intelligence"], "Data Analysis"),
    (["chatbot", "chat assistant", "conversational ai", "virtual assistant"], "AI Assistants"),
    (["creative coding", "generative art"], "Creative"),
    (["vector database", " rag ", "embedding", "retrieval", "llm framework", "inference engine", "model serving",
      "mlops", "observability", "code execution api", "browser sandbox"], "Developer Tools"),
]


class TaxonomyClassifier:
    """
    Classifies Tool records into standardized categories defined in configs/settings.yaml.
    
    Uses evidence-based category inference with semantic corrections:
    - Code execution services (e.g. Judge0) -> Developer Tools / Coding (NOT Agents)
    - Prompt utilities (e.g. prompt-optimizer) -> Productivity / Developer Tools (NOT Models)
    - Browser automation / sandbox -> Agents / Automation / Developer Tools (NOT Models)
    """

    DEFAULT_TAXONOMY = [
        "Productivity", "Developer Tools", "Coding", "Writing", "Design",
        "Video", "Audio", "Research", "Marketing", "Education",
        "Data Analysis", "Automation", "Customer Support", "Image Generation",
        "AI Assistants", "Models", "Agents", "MCP", "Creative"
    ]

    def __init__(self, config_path: str = "configs/settings.yaml"):
        self.categories = self._load_taxonomy(config_path)

    def _load_taxonomy(self, path_str: str) -> List[str]:
        path = Path(path_str)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                    cats = cfg.get("taxonomy", {}).get("categories")
                    if cats and isinstance(cats, list):
                        return cats
            except Exception:
                pass
        return self.DEFAULT_TAXONOMY

    def _infer_from_topics(self, topics: List[str]) -> List[str]:
        """Map GitHub topics to taxonomy categories."""
        inferred = []
        for topic in topics:
            t_lower = topic.lower().strip()
            if t_lower in TOPIC_CATEGORY_MAP:
                cat = TOPIC_CATEGORY_MAP[t_lower]
                if cat in self.categories and cat not in inferred:
                    inferred.append(cat)
        return inferred

    def _infer_from_description(self, text: str) -> List[str]:
        """Infer categories from description and name text using keyword patterns."""
        text_lower = f" {text.lower()} "
        inferred = []
        for keywords, category in DESC_CATEGORY_PATTERNS:
            if category not in self.categories:
                continue
            if any(kw in text_lower for kw in keywords):
                if category not in inferred:
                    inferred.append(category)
        return inferred

    def classify(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates and refines category list for the record with strict semantic rules.
        """
        existing_cats = record.get("categories", [])
        valid_cats = [c for c in existing_cats if c in self.categories]

        inference_reasons = []

        # If we already have valid categories from seed data, keep them
        if valid_cats and record.get("discovery_source_type") == "CURATED_SEED":
            inference_reasons.append(f"Pre-existing seed categories: {valid_cats}")
            record["categories"] = valid_cats
            record["category_inference_reasons"] = inference_reasons
            return record

        # Try GitHub topics first
        topics = record.get("github_topics") or []
        if topics:
            topic_cats = self._infer_from_topics(topics)
            if topic_cats:
                valid_cats.extend(topic_cats)
                inference_reasons.append(f"Inferred from GitHub topics {topics}: {topic_cats}")

        # Then try description + name analysis
        desc_text = (record.get("description") or "").strip()
        name_text = (record.get("name") or "").strip()
        text = f"{desc_text} {name_text}".strip()

        if text:
            desc_cats = self._infer_from_description(text)
            for cat in desc_cats:
                if cat not in valid_cats:
                    valid_cats.append(cat)
                    inference_reasons.append(f"Inferred from description/name: {cat}")

        # Semantic Overrides for Specific Misclassifications:
        text_lower = text.lower()
        
        # 1. Code execution services (e.g., Judge0) -> NOT Agents
        if any(term in text_lower for term in ["code execution", "compiler api", "online judge", "sandbox execution"]):
            if "Agents" in valid_cats:
                valid_cats.remove("Agents")
                inference_reasons.append("Removed 'Agents': code execution service is primary Developer Tools / Coding")
            if "Developer Tools" not in valid_cats and "Coding" not in valid_cats:
                valid_cats.append("Developer Tools")

        # 2. Prompt utilities / optimizers -> NOT Models
        if any(term in text_lower for term in ["prompt optimizer", "prompt optimization", "prompt engineering", "prompt library"]):
            if "Models" in valid_cats:
                valid_cats.remove("Models")
                inference_reasons.append("Removed 'Models': prompt utility is primary Productivity / Developer Tools")
            if "Productivity" not in valid_cats and "Developer Tools" not in valid_cats:
                valid_cats.append("Productivity")

        # 3. Browser automation / sandbox -> NOT Models
        if any(term in text_lower for term in ["browser automation", "browser sandbox", "browser API"]):
            if "Models" in valid_cats:
                valid_cats.remove("Models")
                inference_reasons.append("Removed 'Models': browser automation is primary Automation / Agents")

        # Deduplicate while preserving order
        seen = set()
        deduped_cats = []
        for c in valid_cats:
            if c not in seen:
                seen.add(c)
                deduped_cats.append(c)
        valid_cats = deduped_cats

        # Fallback
        if not valid_cats:
            valid_cats.append("Developer Tools")
            inference_reasons.append("Fallback: no evidence-based category found")

        record["categories"] = valid_cats
        record["category_inference_reasons"] = inference_reasons
        return record
