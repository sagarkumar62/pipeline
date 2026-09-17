import asyncio
import os
import random
from typing import AsyncGenerator, Dict, Any, List, Optional
import httpx
from src.discovery.base import BaseDiscoverySource
from src.utils.logging import setup_logger

logger = setup_logger("device_discovery")


class DevicesAdapter(BaseDiscoverySource):
    """
    Discovery adapter for physical Device ecosystem entities.
    Integrates GitHub API queries targeting AI hardware, edge AI developer kits, AI accelerators,
    AI workstations, AI cameras, AI wearables, and physical AI interfaces while recording source metadata.
    
    INTENDED SOURCES:
    - GitHub AI Hardware Repositories & Open DevKits (Accessible API)
    - Hardware Vendor Portals & AI Device Registries (Inaccessible / Auth-restricted / JavaScript heavy)
    
    ACTUAL SOURCES USED:
    - GitHub AI Hardware & Edge Devices Search API
    """

    @property
    def source_name(self) -> str:
        return "GitHub AI Hardware & Edge Devices Search"

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
            "\"edge ai\" in:name,description stars:>5",
            "\"ai accelerator\" in:name,description stars:>5",
            "\"ai camera\" in:name,description stars:>5",
            "\"ai wearable\" in:name,description stars:>5",
            "\"npu\" devkit in:name,description stars:>5",
            "\"jetson\" in:name,description stars:>10",
            "topic:edge-ai stars:>5",
            "topic:ai-hardware stars:>5",
            "\"ai workstation\" in:name,description stars:>5",
            "\"ai hardware\" platform in:name,description stars:>5"
        ]

    async def discover(self, limit: int = 150) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Asynchronously yields raw candidate Device records from GitHub AI Hardware Search.
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
                        logger.info(f"Querying Device Discovery API: q='{query}' page={page}")
                        response = await client.get(url, params=params)

                        if response.status_code in (403, 429):
                            backoff = 5.0 + random.uniform(0.5, 2.0)
                            logger.warning(f"Device Discovery rate limit hit ({response.status_code}). Backoff {backoff:.1f}s...")
                            await asyncio.sleep(backoff)
                            continue

                        if response.status_code != 200:
                            logger.error(f"Device Discovery API status {response.status_code}: {response.text[:150]}")
                            break

                        data = response.json()
                        items = data.get("items", [])
                        if not items:
                            break

                        for item in items:
                            item["_discovery_query"] = query
                            item["_discovery_source"] = "GitHub AI Hardware Search"
                            item["_discovery_type"] = "API"
                            yield item
                            yielded_count += 1
                            if yielded_count >= limit:
                                break

                        await asyncio.sleep(1.0 + random.uniform(0.1, 0.5))

                    except Exception as e:
                        logger.error(f"Network error during Device discovery: {e}")
                        await asyncio.sleep(2.0)
                        break

        logger.info(f"DevicesAdapter finished discovery. Total candidates yielded: {yielded_count}")
