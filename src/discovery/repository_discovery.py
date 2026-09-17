import asyncio
import os
from typing import AsyncGenerator, Dict, Any, List, Optional
import httpx
from src.discovery.base import BaseDiscoverySource
from src.utils.logging import setup_logger

logger = setup_logger("repository_discovery")


class RepositoriesAdapter(BaseDiscoverySource):
    """
    Discovery adapter for software repository entities using GitHub API.
    Reuses HTTP client infrastructure, rate limiting, retry/backoff, and pagination.
    
    Priority Search Queries for AI & Software Repositories:
    - topic:ai-framework stars:>100
    - topic:agent-framework stars:>100
    - topic:machine-learning-library stars:>200
    - topic:deep-learning stars:>500
    - topic:vector-search stars:>100
    - topic:llm-inference stars:>100
    - topic:mcp-server stars:>50
    """

    @property
    def source_name(self) -> str:
        return "GitHub API (Repositories Adapter)"

    def __init__(
        self,
        queries: Optional[List[str]] = None,
        max_pages_per_query: int = 2,
        per_page: int = 50,
        github_token: Optional[str] = None
    ):
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self.max_pages_per_query = max_pages_per_query
        self.per_page = per_page
        self.queries = queries or [
            "topic:ai-framework stars:100..5000",
            "topic:agent-framework stars:>100",
            "topic:machine-learning-library stars:>200",
            "topic:vector-search stars:>100",
            "topic:llm-inference stars:>200",
            "topic:mcp-server stars:>50"
        ]

    async def discover(self, limit: int = 150) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Asynchronously fetches and yields raw repository candidates from GitHub API.
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
                        logger.info(f"Querying GitHub Repositories API: q='{query}' page={page}")
                        response = await client.get(url, params=params)

                        if response.status_code == 403:
                            logger.warning("GitHub API rate limit hit (403). Sleeping for backoff...")
                            await asyncio.sleep(5.0)
                            continue

                        if response.status_code != 200:
                            logger.error(f"GitHub API error {response.status_code}: {response.text[:200]}")
                            break

                        data = response.json()
                        items = data.get("items", [])
                        if not items:
                            logger.info(f"No more items returned for query '{query}'")
                            break

                        for item in items:
                            item["_discovery_query"] = query
                            item["_discovery_source"] = self.source_name
                            yield item
                            yielded_count += 1
                            if yielded_count >= limit:
                                break

                        # Gentle rate limiting between pages
                        await asyncio.sleep(1.0)

                    except Exception as e:
                        logger.error(f"HTTP exception during GitHub API discovery: {e}")
                        await asyncio.sleep(2.0)
                        break

        logger.info(f"RepositoriesAdapter finished discovery. Total candidates yielded: {yielded_count}")
