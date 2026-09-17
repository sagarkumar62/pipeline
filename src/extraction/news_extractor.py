import re
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from email.utils import parsedate_to_datetime

from src.models.news import NewsRecord
from src.utils.urls import normalize_url, extract_domain
from src.utils.logging import setup_logger

logger = setup_logger("news_extractor")

# List of tracking query parameters to strip for clean canonical URLs
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "msclkid", "ref", "mc_cid", "mc_eid", "source", "_hsenc", "_hsmi"
}

AI_TAXONOMY_KEYWORDS = {
    "AI Models": ["model", "llm", "gpt", "claude", "gemini", "llama", "deepseek", "mistral", "transformer", "diffusion", "bfloat16", "fp8", "neural network"],
    "Generative AI": ["generative ai", "genai", "text-to-image", "rag", "prompt", "fine-tuning", "synthetic data"],
    "Agents": ["agent", "multi-agent", "autonomous agent", "copilot", "mcp", "tool use", "reasoning"],
    "Robotics": ["robot", "robotics", "humanoid", "quadruped", "manipulator", "drone", "autonomous vehicle", "ros 2"],
    "AI Hardware": ["npu", "gpu", "tpu", "chip", "semiconductor", "nvidia", "hailo", "jetson", "coral tpu", "edge ai", "silicon", "accelerator"],
    "Developer Tools": ["sdk", "api", "framework", "pytorch", "tensorflow", "onnx", "langchain", "vllm", "ollama", "huggingface"],
    "Research": ["arxiv", "paper", "benchmark", "dataset", "ablation", "state-of-the-art", "sota", "architecture"],
    "Companies": ["openai", "google", "meta", "microsoft", "nvidia", "anthropic", "amazon", "apple", "mistral", "cohere"],
    "Policy & Security": ["regulation", "copyright", "policy", "safety", "alignment", "jailbreak", "security", "watermark", "governance"]
}


class NewsExtractor:
    """
    Strips HTML noise, normalizes URLs, parses publication dates, extracts categories/entities,
    and constructs canonical NewsRecord dictionaries.
    """

    @staticmethod
    def strip_html_tags(text: str) -> str:
        """Removes HTML markup tags, CDATA blocks, and unescapes entities."""
        if not text:
            return ""
        # Remove CDATA
        text = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", text, flags=re.DOTALL)
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Unescape HTML entities
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def canonicalize_article_url(url: str) -> Tuple[str, str]:
        """
        Normalizes article URL by stripping tracking parameters, normalizing scheme/host.
        Returns: Tuple[canonical_url, domain]
        """
        if not url:
            return "", ""

        try:
            parsed = urlparse(url.strip())
            scheme = parsed.scheme.lower() or "https"
            netloc = parsed.netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]

            # Filter query parameters
            query_dict = parse_qs(parsed.query, keep_blank_values=False)
            filtered_query = {k: v for k, v in query_dict.items() if k.lower() not in TRACKING_PARAMS}
            clean_query = urlencode(filtered_query, doseq=True)

            path = parsed.path
            # Normalize trailing slash except for root path
            if len(path) > 1 and path.endswith("/"):
                path = path[:-1]

            canonical_url = urlunparse((scheme, netloc, path, parsed.params, clean_query, ""))
            domain = extract_domain(canonical_url) or netloc
            return canonical_url, domain
        except Exception:
            norm = normalize_url(url)
            return norm, extract_domain(norm)

    @staticmethod
    def parse_publication_date(date_str: str) -> datetime:
        """Parses various date string formats into standard UTC datetime object."""
        if not date_str or not date_str.strip():
            return datetime.now(timezone.utc)

        date_str = date_str.strip()

        # Try ISO format
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc)
        except Exception:
            pass

        # Try RFC 2822 format (standard for RSS)
        try:
            tp = parsedate_to_datetime(date_str)
            if tp is not None:
                return tp.astimezone(timezone.utc)
        except Exception:
            pass

        # Try common date formats
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT"):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except Exception:
                continue

        return datetime.now(timezone.utc)

    @classmethod
    def classify_categories_and_entities(cls, title: str, summary: str) -> Tuple[List[str], List[str]]:
        """
        Classifies taxonomy categories and extracts key named entities based on content keywords.
        """
        combined = f"{title.lower()} {summary.lower()}"
        assigned_categories: List[str] = []
        extracted_entities: List[str] = []

        for category, keywords in AI_TAXONOMY_KEYWORDS.items():
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", combined):
                    if category not in assigned_categories:
                        assigned_categories.append(category)
                    if category == "Companies" and kw.capitalize() not in extracted_entities:
                        extracted_entities.append(kw.capitalize())

        if not assigned_categories:
            assigned_categories.append("General AI")

        return assigned_categories, extracted_entities

    def extract_record(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforms a raw feed item into a structured News candidate record dictionary.
        """
        raw_title = raw_item.get("title", "")
        clean_title = self.strip_html_tags(raw_title)
        canonical_title = re.sub(r"\s+", " ", clean_title).strip()

        raw_url = raw_item.get("url", "")
        canonical_url, domain = self.canonicalize_article_url(raw_url)

        raw_summary = raw_item.get("summary", "")
        clean_summary = self.strip_html_tags(raw_summary)

        pub_date_str = raw_item.get("pub_date", "")
        published_at = self.parse_publication_date(pub_date_str)

        categories, entities = self.classify_categories_and_entities(canonical_title, clean_summary)

        canonical_url_hash = NewsRecord.compute_canonical_url_hash(canonical_url)
        content_hash = NewsRecord.compute_content_hash(canonical_title, clean_summary[:200])

        source_name = raw_item.get("source_name") or domain
        source_id = raw_item.get("source_id", "src_unknown")

        # Stable ID based on canonical URL hash
        entity_id = f"news:{canonical_url_hash[:16]}"

        provenance = {
            "source_id": source_id,
            "feed_url": raw_item.get("feed_url", ""),
            "raw_url": raw_url,
            "canonical_url": canonical_url,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "has_raw_date": bool(pub_date_str)
        }

        return {
            "id": entity_id,
            "entity_type": "news",
            "name": clean_title,
            "title": clean_title,
            "canonical_title": canonical_title,
            "url": canonical_url,
            "canonical_url": canonical_url,
            "source_name": source_name,
            "source_domain": domain,
            "source_url": raw_url,
            "published_at": published_at.isoformat(),
            "author": raw_item.get("author") or None,
            "summary": clean_summary[:500] if clean_summary else "",
            "content_excerpt": clean_summary[:1000] if clean_summary else None,
            "categories": categories,
            "entities": entities,
            "topics": categories,
            "tags": raw_item.get("categories") or [],
            "language": "en",
            "article_type": "NEWS_ARTICLE",
            "status": "QUALIFIED",
            "discovery_source": {
                "name": source_name,
                "url": raw_item.get("feed_url", raw_url),
                "source_type": "RSS_FEED",
                "source_trust_level": "HIGH"
            },
            "source": {
                "name": source_name,
                "url": raw_item.get("feed_url", raw_url),
                "source_type": "RSS_FEED",
                "source_trust_level": "HIGH"
            },
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "last_verified": datetime.now(timezone.utc).isoformat(),
            "provenance": provenance,
            "content_hash": content_hash,
            "canonical_url_hash": canonical_url_hash,
            "event_cluster_id": None
        }
