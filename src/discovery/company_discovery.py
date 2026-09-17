import asyncio
import os
import random
from typing import AsyncGenerator, Dict, Any, List, Optional
import httpx
from src.discovery.base import BaseDiscoverySource
from src.utils.logging import setup_logger

logger = setup_logger("company_discovery")


class CompanyAdapter(BaseDiscoverySource):
    """
    Discovery adapter for AI Company ecosystem entities.
    Queries GitHub Organizations API and fetches detailed corporate profiles including
    official blog/website URLs, locations, and descriptions.
    """

    @property
    def source_name(self) -> str:
        return "GitHub Organizations & AI Directories Adapter"

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
            "type:org ai in:login,name",
            "type:org artificial-intelligence in:login,name",
            "type:org machine-learning in:login,name",
            "type:org llm in:login,name",
            "type:org autonomous-agent in:login,name"
        ]

    async def _fetch_org_detail(self, client: httpx.AsyncClient, login: str) -> Dict[str, Any]:
        """Fetches detailed profile for an organization including blog URL and description."""
        url = f"https://api.github.com/orgs/{login}"
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning(f"Failed to fetch org detail for {login}: {e}")
        return {}

    async def discover(self, limit: int = 150) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Asynchronously yields raw candidate Company records with detailed org profiles.
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Orbit-Pipeline/1.0 (+https://ai-orbit.org)"
        }
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        yielded_count = 0
        seen_logins = set()

        async with httpx.AsyncClient(headers=headers, timeout=15.0, follow_redirects=True) as client:
            for query in self.queries:
                if yielded_count >= limit:
                    break

                for page in range(1, self.max_pages_per_query + 1):
                    if yielded_count >= limit:
                        break

                    url = "https://api.github.com/search/users"
                    params = {
                        "q": query,
                        "sort": "followers",
                        "order": "desc",
                        "per_page": min(self.per_page, limit - yielded_count),
                        "page": page
                    }

                    try:
                        logger.info(f"Querying Company Discovery API: q='{query}' page={page}")
                        response = await client.get(url, params=params)

                        if response.status_code in (403, 429):
                            backoff = 5.0 + random.uniform(0.5, 2.0)
                            logger.warning(f"Company Discovery rate limit hit ({response.status_code}). Backoff {backoff:.1f}s...")
                            await asyncio.sleep(backoff)
                            continue

                        if response.status_code != 200:
                            logger.error(f"Company Discovery API status {response.status_code}: {response.text[:150]}")
                            break

                        data = response.json()
                        items = data.get("items", [])
                        if not items:
                            break

                        for item in items:
                            login = item.get("login")
                            if not login or login in seen_logins:
                                continue
                            seen_logins.add(login)

                            # Fetch org detail to get website/blog and description
                            detail = await self._fetch_org_detail(client, login)
                            merged_item = {**item, **detail}
                            merged_item["_discovery_query"] = query
                            merged_item["_discovery_source"] = "GitHub Organizations API"
                            merged_item["_discovery_type"] = "API"

                            yield merged_item
                            yielded_count += 1
                            if yielded_count >= limit:
                                break

                        await asyncio.sleep(0.5)

                    except Exception as e:
                        logger.error(f"Network error during Company discovery: {e}")
                        await asyncio.sleep(2.0)
                        break

        logger.info(f"CompanyAdapter finished discovery. Total candidates yielded: {yielded_count}")
