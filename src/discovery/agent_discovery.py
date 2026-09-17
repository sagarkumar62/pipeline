import asyncio
import os
import random
from typing import AsyncGenerator, Dict, Any, List, Optional
import httpx
from src.discovery.base import BaseDiscoverySource
from src.utils.logging import setup_logger

logger = setup_logger("agent_discovery")


class AgentsAdapter(BaseDiscoverySource):
    """
    Discovery adapter for AI Agent ecosystem entities.
    Integrates GitHub API queries targeting concrete AI Agent implementations, framework packages,
    and agentic platforms while recording source metadata.
    """

    @property
    def source_name(self) -> str:
        return "GitHub API & Agent Registries Adapter"

    def __init__(
        self,
        queries: Optional[List[str]] = None,
        max_pages_per_query: int = 2,
        per_page: int = 30,
        github_token: Optional[str] = None
    ):
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self.max_pages_per_query = max_pages_per_query
        self.per_page = per_page
        self.queries = queries or [
            "topic:ai-agent stars:>10",
            "topic:autonomous-agent stars:>10",
            "topic:agent-framework stars:>15",
            "topic:coding-agent stars:>10",
            "topic:browser-agent stars:>5",
            "topic:multi-agent stars:>10",
            "topic:agentic-ai stars:>10",
            "topic:ai-agents stars:>10"
        ]

    async def discover(self, limit: int = 150) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Asynchronously yields raw candidate Agent records from GitHub and public sources.
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Orbit-Pipeline/1.0 (+https://ai-orbit.org)"
        }
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        yielded_count = 0

        async with httpx.AsyncClient(headers=headers, timeout=15.0, follow_redirects=True) as client:
            for query in self.queries:
                if yielded_count >= limit:
                    break

                for page in range(1, self.max_pages_per_query + 1):
                    if yielded_count >= limit:
                        break

                    url = "https://api.github.com/search/repositories"
                    params = {
                        "q": query,
                        "sort": "stars",
                        "order": "desc",
                        "per_page": min(self.per_page, limit - yielded_count),
                        "page": page
                    }

                    try:
                        logger.info(f"Querying Agent Discovery API: q='{query}' page={page}")
                        response = await client.get(url, params=params)

                        if response.status_code in (403, 429):
                            backoff = 5.0 + random.uniform(0.5, 2.0)
                            logger.warning(f"Agent Discovery rate limit hit ({response.status_code}). Backoff {backoff:.1f}s...")
                            await asyncio.sleep(backoff)
                            continue

                        if response.status_code != 200:
                            logger.error(f"Agent Discovery API status {response.status_code}: {response.text[:150]}")
                            break

                        data = response.json()
                        items = data.get("items", [])
                        if not items:
                            break

                        for item in items:
                            item["_discovery_query"] = query
                            item["_discovery_source"] = "GitHub Agent Search"
                            item["_discovery_type"] = "API"
                            yield item
                            yielded_count += 1
                            if yielded_count >= limit:
                                break

                        # Rate limiting jitter delay
                        await asyncio.sleep(1.0 + random.uniform(0.1, 0.5))

                    except Exception as e:
                        logger.error(f"Network error during Agent discovery: {e}")
                        await asyncio.sleep(2.0)
                        break

        logger.info(f"AgentsAdapter finished discovery. Total candidates yielded: {yielded_count}")
