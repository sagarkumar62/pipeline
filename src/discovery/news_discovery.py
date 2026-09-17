import time
from datetime import datetime, timezone
import logging
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple
import requests

from src.models.news import NewsSource
from src.utils.logging import setup_logger

logger = setup_logger("news_discovery")

# -------------------------------------------------------------------------
# CURATED NEWS SOURCE REGISTRY (25+ High Quality Public Feeds)
# -------------------------------------------------------------------------
CURATED_NEWS_SOURCES: List[Dict[str, Any]] = [
    {
        "source_id": "src_arxiv_cs_ai",
        "source_name": "arXiv Computer Science - Artificial Intelligence",
        "source_type": "RSS_FEED",
        "feed_url": "https://rss.arxiv.org/rss/cs.AI",
        "publisher_domain": "arxiv.org",
        "notes": "Official open-access research preprints for AI"
    },
    {
        "source_id": "src_arxiv_cs_cv",
        "source_name": "arXiv Computer Science - Computer Vision",
        "source_type": "RSS_FEED",
        "feed_url": "https://rss.arxiv.org/rss/cs.CV",
        "publisher_domain": "arxiv.org",
        "notes": "Official open-access research preprints for Vision & Multimodal AI"
    },
    {
        "source_id": "src_arxiv_cs_cl",
        "source_name": "arXiv Computer Science - Computation & Language",
        "source_type": "RSS_FEED",
        "feed_url": "https://rss.arxiv.org/rss/cs.CL",
        "publisher_domain": "arxiv.org",
        "notes": "Official open-access research preprints for LLMs and NLP"
    },
    {
        "source_id": "src_mit_tech_review",
        "source_name": "MIT Technology Review - AI",
        "source_type": "RSS_FEED",
        "feed_url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
        "publisher_domain": "technologyreview.com",
        "notes": "Leading technology & AI news publication"
    },
    {
        "source_id": "src_techcrunch_ai",
        "source_name": "TechCrunch Artificial Intelligence",
        "source_type": "RSS_FEED",
        "feed_url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "publisher_domain": "techcrunch.com",
        "notes": "Major technology, AI startup & product launch news"
    },
    {
        "source_id": "src_venturebeat_ai",
        "source_name": "VentureBeat AI",
        "source_type": "RSS_FEED",
        "feed_url": "https://venturebeat.com/category/ai/feed/",
        "publisher_domain": "venturebeat.com",
        "notes": "Enterprise AI & Machine Learning news publication"
    },
    {
        "source_id": "src_hackernews_ai",
        "source_name": "Hacker News Feed",
        "source_type": "RSS_FEED",
        "feed_url": "https://news.ycombinator.com/rss",
        "publisher_domain": "ycombinator.com",
        "notes": "Developer & AI community news aggregator"
    },
    {
        "source_id": "src_openai_blog",
        "source_name": "OpenAI Official News & Blog",
        "source_type": "RSS_FEED",
        "feed_url": "https://openai.com/news/rss.xml",
        "publisher_domain": "openai.com",
        "notes": "Official OpenAI research & product announcements"
    },
    {
        "source_id": "src_google_ai_blog",
        "source_name": "Google DeepMind & Research Blog",
        "source_type": "RSS_FEED",
        "feed_url": "https://blog.google/technology/ai/rss/",
        "publisher_domain": "blog.google",
        "notes": "Official Google & DeepMind AI research blog"
    },
    {
        "source_id": "src_huggingface_blog",
        "source_name": "Hugging Face Blog",
        "source_type": "RSS_FEED",
        "feed_url": "https://huggingface.co/blog/feed.xml",
        "publisher_domain": "huggingface.co",
        "notes": "Official open-source AI community & model releases"
    },
    {
        "source_id": "src_nvidia_blog",
        "source_name": "NVIDIA AI Blog",
        "source_type": "RSS_FEED",
        "feed_url": "https://blogs.nvidia.com/feed/",
        "publisher_domain": "nvidia.com",
        "notes": "Official NVIDIA AI & computing hardware news"
    },
    {
        "source_id": "src_aws_ai_blog",
        "source_name": "AWS Machine Learning Blog",
        "source_type": "RSS_FEED",
        "feed_url": "https://aws.amazon.com/blogs/machine-learning/feed/",
        "publisher_domain": "aws.amazon.com",
        "notes": "Official Amazon Web Services AI & ML blog"
    },
    {
        "source_id": "src_microsoft_ai",
        "source_name": "Microsoft Official AI Blog",
        "source_type": "RSS_FEED",
        "feed_url": "https://blogs.microsoft.com/ai/feed/",
        "publisher_domain": "blogs.microsoft.com",
        "notes": "Official Microsoft AI research & cloud news"
    },
    {
        "source_id": "src_meta_ai",
        "source_name": "Meta AI Research",
        "source_type": "RSS_FEED",
        "feed_url": "https://ai.meta.com/blog/rss.xml",
        "publisher_domain": "ai.meta.com",
        "notes": "Official Meta FAIR research & open model announcements"
    },
    {
        "source_id": "src_bair_blog",
        "source_name": "Berkeley AI Research (BAIR) Blog",
        "source_type": "RSS_FEED",
        "feed_url": "https://bair.berkeley.edu/blog/feed.xml",
        "publisher_domain": "bair.berkeley.edu",
        "notes": "UC Berkeley AI research lab technical blog"
    },
    {
        "source_id": "src_wired_ai",
        "source_name": "WIRED Artificial Intelligence",
        "source_type": "RSS_FEED",
        "feed_url": "https://www.wired.com/feed/tag/ai/latest/rss",
        "publisher_domain": "wired.com",
        "notes": "Major technology & AI policy publication"
    },
    {
        "source_id": "src_ars_technica_ai",
        "source_name": "Ars Technica AI & Tech",
        "source_type": "RSS_FEED",
        "feed_url": "https://feeds.arstechnica.com/arstechnica/index",
        "publisher_domain": "arstechnica.com",
        "notes": "Technical reporting on AI and computing"
    },
    {
        "source_id": "src_slashdot_ai",
        "source_name": "Slashdot Tech News",
        "source_type": "RSS_FEED",
        "feed_url": "https://rss.slashdot.org/Slashdot/slashdotMain",
        "publisher_domain": "slashdot.org",
        "notes": "Long-running tech & open source community news"
    },
    {
        "source_id": "src_infoq_ai",
        "source_name": "InfoQ AI, ML & Data Engineering",
        "source_type": "RSS_FEED",
        "feed_url": "https://feed.infoq.com/ai-ml-data-eng/news/",
        "publisher_domain": "infoq.com",
        "notes": "Software development & enterprise AI reporting"
    },
    {
        "source_id": "src_marktechpost",
        "source_name": "MarkTechPost AI News",
        "source_type": "RSS_FEED",
        "feed_url": "https://www.marktechpost.com/feed/",
        "publisher_domain": "marktechpost.com",
        "notes": "Daily summaries of AI paper releases & tools"
    },
    {
        "source_id": "src_ai_trends",
        "source_name": "AI Trends News",
        "source_type": "RSS_FEED",
        "feed_url": "https://www.aitrends.com/feed/",
        "publisher_domain": "aitrends.com",
        "notes": "Enterprise AI & industrial adoption reporting"
    },
    {
        "source_id": "src_sdtimes_ai",
        "source_name": "SD Times Software & AI",
        "source_type": "RSS_FEED",
        "feed_url": "https://www.sdtimes.com/feed/",
        "publisher_domain": "sdtimes.com",
        "notes": "Software development tools and AI integration"
    },
    {
        "source_id": "src_kdnuggets",
        "source_name": "KDnuggets Data Science & AI",
        "source_type": "RSS_FEED",
        "feed_url": "https://www.kdnuggets.com/feed",
        "publisher_domain": "kdnuggets.com",
        "notes": "Data science, AI models & developer tutorials"
    },
    {
        "source_id": "src_towardsdatascience",
        "source_name": "Towards Data Science Feed",
        "source_type": "RSS_FEED",
        "feed_url": "https://towardsdatascience.com/feed",
        "publisher_domain": "towardsdatascience.com",
        "notes": "Technical articles on AI, ML, and data architecture"
    },
    {
        "source_id": "src_the_register_ai",
        "source_name": "The Register Biting Tech News",
        "source_type": "RSS_FEED",
        "feed_url": "https://www.theregister.com/software/ai_ml/headlines.atom",
        "publisher_domain": "theregister.com",
        "notes": "Enterprise tech & AI hardware reporting"
    }
]


class NewsDiscoveryEngine:
    """
    Ingests AI news candidates from curated public RSS, Atom, and API feeds.
    Implements rate limiting, retries, user-agent headers, and robust XML parsing.
    """

    def __init__(self, sources: Optional[List[Dict[str, Any]]] = None):
        self.sources = sources or CURATED_NEWS_SOURCES
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AIOrbitPipeline/1.0 (Public AI Research Ingestion)"
        }

    def get_source_registry(self) -> List[Dict[str, Any]]:
        """Returns the full source registry list."""
        return self.sources

    def parse_feed_xml(self, xml_content: str, source_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parses XML string representing an RSS 2.0 or Atom feed into standard raw article dictionaries.
        """
        items: List[Dict[str, Any]] = []
        if not xml_content or not xml_content.strip():
            return items

        try:
            # Clean string encoding issues if any
            clean_xml = xml_content.strip()
            # Parse XML tree
            root = ET.fromstring(clean_xml)

            # Detect format: RSS vs Atom
            tag = root.tag.lower()
            if "rss" in tag or root.find("channel") is not None:
                channel = root.find("channel")
                channel_elem = channel if channel is not None else root
                for elem in channel_elem.findall("item"):
                    title = (elem.findtext("title") or "").strip()
                    link = (elem.findtext("link") or "").strip()
                    description = (elem.findtext("description") or elem.findtext("{http://purl.org/rss/1.0/modules/content/}encoded") or "").strip()
                    pub_date = (elem.findtext("pubDate") or elem.findtext("{http://purl.org/dc/elements/1.1/}date") or "").strip()
                    author = (elem.findtext("author") or elem.findtext("{http://purl.org/dc/elements/1.1/}creator") or "").strip()

                    categories = [cat.text.strip() for cat in elem.findall("category") if cat.text]

                    if title and link:
                        items.append({
                            "title": title,
                            "url": link,
                            "summary": description,
                            "pub_date": pub_date,
                            "author": author,
                            "categories": categories,
                            "source_name": source_info["source_name"],
                            "source_domain": source_info["publisher_domain"],
                            "source_id": source_info["source_id"],
                            "feed_url": source_info["feed_url"]
                        })
            else:
                # Atom format parsing
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                # Try finding entries both with namespace and without namespace
                entries = root.findall("atom:entry", ns) or root.findall("entry")
                for entry in entries:
                    title_elem = entry.find("atom:title", ns) or entry.find("title")
                    title = (title_elem.text if title_elem is not None and title_elem.text else "").strip()

                    link = ""
                    for l in (entry.findall("atom:link", ns) or entry.findall("link")):
                        if l.get("rel") == "alternate" or not l.get("rel"):
                            link = l.get("href", "")
                            if link:
                                break

                    summary_elem = entry.find("atom:summary", ns) or entry.find("summary") or entry.find("atom:content", ns) or entry.find("content")
                    summary = (summary_elem.text if summary_elem is not None and summary_elem.text else "").strip()

                    updated_elem = entry.find("atom:updated", ns) or entry.find("updated") or entry.find("atom:published", ns) or entry.find("published")
                    pub_date = (updated_elem.text if updated_elem is not None and updated_elem.text else "").strip()

                    author_elem = entry.find("atom:author/atom:name", ns) or entry.find("author/name")
                    author = (author_elem.text if author_elem is not None and author_elem.text else "").strip()

                    if title and link:
                        items.append({
                            "title": title,
                            "url": link,
                            "summary": summary,
                            "pub_date": pub_date,
                            "author": author,
                            "categories": [],
                            "source_name": source_info["source_name"],
                            "source_domain": source_info["publisher_domain"],
                            "source_id": source_info["source_id"],
                            "feed_url": source_info["feed_url"]
                        })
        except Exception as e:
            logger.warning(f"XML ET parser exception for {source_info['source_name']}: {e}. Trying regex fallback parser.")
            items = self._regex_xml_fallback(xml_content, source_info)

        return items

    def _regex_xml_fallback(self, xml_content: str, source_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback regex parser for non-standard XML feeds."""
        items: List[Dict[str, Any]] = []
        item_blocks = re.findall(r"<item>(.*?)</item>", xml_content, re.DOTALL | re.IGNORECASE)
        if not item_blocks:
            item_blocks = re.findall(r"<entry>(.*?)</entry>", xml_content, re.DOTALL | re.IGNORECASE)

        for block in item_blocks:
            title_m = re.search(r"<title>(.*?)</title>", block, re.DOTALL | re.IGNORECASE)
            link_m = re.search(r"<link>(.*?)</link>", block, re.DOTALL | re.IGNORECASE)
            if not link_m:
                link_m = re.search(r'href=["\']([^"\']+)["\']', block, re.IGNORECASE)
            desc_m = re.search(r"<description>(.*?)</description>", block, re.DOTALL | re.IGNORECASE)
            pub_m = re.search(r"<(?:pubDate|updated|published)>(.*?)</(?:pubDate|updated|published)>", block, re.DOTALL | re.IGNORECASE)

            title = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", title_m.group(1)).strip() if title_m else ""
            link = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", link_m.group(1)).strip() if link_m else ""
            summary = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", desc_m.group(1)).strip() if desc_m else ""
            pub_date = pub_m.group(1).strip() if pub_m else ""

            if title and link:
                items.append({
                    "title": title,
                    "url": link,
                    "summary": summary,
                    "pub_date": pub_date,
                    "author": "",
                    "categories": [],
                    "source_name": source_info["source_name"],
                    "source_domain": source_info["publisher_domain"],
                    "source_id": source_info["source_id"],
                    "feed_url": source_info["feed_url"]
                })
        return items

    def fetch_source_feed(self, source_info: Dict[str, Any], timeout: int = 12) -> Tuple[List[Dict[str, Any]], str]:
        """
        Fetches a single feed source safely via HTTP GET.
        Returns Tuple[items, status]: status in ("SUCCESS", "TIMEOUT", "ACCESS_BLOCKED", "PARSE_ERROR", "HTTP_ERROR")
        """
        feed_url = source_info["feed_url"]
        logger.info(f"Fetching news feed from: '{source_info['source_name']}' ({feed_url})")

        try:
            resp = requests.get(feed_url, headers=self.headers, timeout=timeout)
            if resp.status_code == 200:
                items = self.parse_feed_xml(resp.text, source_info)
                if items:
                    return items, "SUCCESS"
                else:
                    return [], "PARSE_ERROR"
            elif resp.status_code in (403, 401, 429):
                logger.warning(f"Source access blocked ({resp.status_code}): {feed_url}")
                return [], "ACCESS_BLOCKED"
            else:
                logger.warning(f"HTTP error {resp.status_code} fetching feed: {feed_url}")
                return [], f"HTTP_{resp.status_code}"
        except requests.Timeout:
            logger.warning(f"Timeout fetching feed: {feed_url}")
            return [], "TIMEOUT"
        except Exception as e:
            logger.warning(f"Error fetching feed {feed_url}: {e}")
            return [], "FETCH_ERROR"

    def discover_all_news(self, max_items_per_source: int = 35) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Discovers news articles across all registered sources.
        Returns: Tuple[raw_candidates, updated_source_registry]
        """
        all_candidates: List[Dict[str, Any]] = []
        registry_status: List[Dict[str, Any]] = []

        for source in self.sources:
            items, status = self.fetch_source_feed(source)

            registry_entry = dict(source)
            registry_entry["status"] = "ACTIVE" if status == "SUCCESS" else status
            registry_entry["last_checked"] = datetime.now(timezone.utc).isoformat()
            registry_entry["items_retrieved"] = len(items)
            registry_status.append(registry_entry)

            # Cap items per source if needed
            capped_items = items[:max_items_per_source]
            all_candidates.extend(capped_items)

            # Politeness delay
            time.sleep(0.3)

        logger.info(f"Discovered a total of {len(all_candidates)} raw candidate articles across {len(self.sources)} sources.")
        return all_candidates, registry_status
