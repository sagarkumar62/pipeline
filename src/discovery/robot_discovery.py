import asyncio
import os
import random
from typing import AsyncGenerator, Dict, Any, List, Optional
import httpx
from src.discovery.base import BaseDiscoverySource
from src.utils.logging import setup_logger

logger = setup_logger("robot_discovery")


class RobotsAdapter(BaseDiscoverySource):
    """
    Discovery adapter for physical Robot ecosystem entities.
    Integrates GitHub API queries targeting concrete physical robotic platforms, humanoid robots,
    quadrupeds, industrial arms, and open robotics hardware implementations while recording source metadata.
    """

    @property
    def source_name(self) -> str:
        return "GitHub Robotics & Open Hardware Adapter"

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
            "topic:humanoid-robot stars:>5",
            "topic:quadruped stars:>5",
            "topic:robotics stars:>20",
            "topic:mobile-robot stars:>5",
            "topic:ros-robot stars:>5",
            "\"humanoid robot\" in:name,description stars:>10",
            "\"quadruped robot\" in:name,description stars:>10",
            "\"robotic arm\" in:name,description stars:>15"
        ]

    async def discover(self, limit: int = 150) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Asynchronously yields raw candidate Robot records from GitHub Robotics & Hardware Search.
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
                        logger.info(f"Querying Robot Discovery API: q='{query}' page={page}")
                        response = await client.get(url, params=params)

                        if response.status_code in (403, 429):
                            backoff = 5.0 + random.uniform(0.5, 2.0)
                            logger.warning(f"Robot Discovery rate limit hit ({response.status_code}). Backoff {backoff:.1f}s...")
                            await asyncio.sleep(backoff)
                            continue

                        if response.status_code != 200:
                            logger.error(f"Robot Discovery API status {response.status_code}: {response.text[:150]}")
                            break

                        data = response.json()
                        items = data.get("items", [])
                        if not items:
                            break

                        for item in items:
                            item["_discovery_query"] = query
                            item["_discovery_source"] = "GitHub Robotics Search"
                            item["_discovery_type"] = "API"
                            yield item
                            yielded_count += 1
                            if yielded_count >= limit:
                                break

                        await asyncio.sleep(1.0 + random.uniform(0.1, 0.5))

                    except Exception as e:
                        logger.error(f"Network error during Robot discovery: {e}")
                        await asyncio.sleep(2.0)
                        break

        logger.info(f"RobotsAdapter finished discovery. Total candidates yielded: {yielded_count}")
