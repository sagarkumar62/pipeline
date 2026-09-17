import asyncio
import os
import random
from typing import AsyncGenerator, Dict, Any, List, Optional
import httpx
from src.discovery.base import BaseDiscoverySource
from src.utils.logging import setup_logger

logger = setup_logger("model_discovery")


class ModelsAdapter(BaseDiscoverySource):
    """
    Discovery adapter for AI Model ecosystem entities.
    Queries OpenRouter API, Hugging Face API, and GitHub API for model cards,
    architectures, and foundation model listings.
    """

    @property
    def source_name(self) -> str:
        return "OpenRouter API, HuggingFace & GitHub Models Adapter"

    def __init__(
        self,
        openrouter_endpoint: str = "https://openrouter.ai/api/v1/models",
        hf_endpoint: str = "https://huggingface.co/api/models",
        github_token: Optional[str] = None
    ):
        self.openrouter_endpoint = openrouter_endpoint
        self.hf_endpoint = hf_endpoint
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")

    async def discover(self, limit: int = 1500) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Asynchronously yields raw candidate Model records from OpenRouter API, Hugging Face, and GitHub.
        """
        headers = {
            "Accept": "application/json",
            "User-Agent": "AI-Orbit-Pipeline/1.0 (+https://ai-orbit.org)"
        }

        yielded_count = 0
        seen_keys = set()

        async with httpx.AsyncClient(headers=headers, timeout=20.0, follow_redirects=True) as client:
            # 1. Discover via OpenRouter API
            try:
                logger.info(f"Querying OpenRouter API endpoint: {self.openrouter_endpoint}")
                resp = await client.get(self.openrouter_endpoint)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("data", [])
                    logger.info(f"OpenRouter returned {len(items)} model items.")
                    for item in items:
                        if yielded_count >= limit:
                            break
                        item_id = item.get("id")
                        if item_id and item_id not in seen_keys:
                            seen_keys.add(item_id)
                            item["_discovery_source"] = "OpenRouter API"
                            item["_discovery_query"] = self.openrouter_endpoint
                            yield item
                            yielded_count += 1
            except Exception as e:
                logger.error(f"Error querying OpenRouter API: {e}")

            # 2. Discover via Hugging Face API across multiple task pipelines
            hf_pipelines = [
                "text-generation",
                "text-to-image",
                "automatic-speech-recognition",
                "image-to-text",
                "text-to-video",
                "text-to-speech",
                "fill-mask",
                "feature-extraction"
            ]

            for pipeline in hf_pipelines:
                if yielded_count >= limit:
                    break
                try:
                    hf_url = f"{self.hf_endpoint}?filter={pipeline}&sort=downloads&direction=-1&limit=100"
                    logger.info(f"Querying Hugging Face API for pipeline: {pipeline}")
                    resp = await client.get(hf_url)
                    if resp.status_code == 200:
                        items = resp.json()
                        logger.info(f"Hugging Face returned {len(items)} items for {pipeline}.")
                        for item in items:
                            if yielded_count >= limit:
                                break
                            item_id = item.get("id") or item.get("modelId")
                            if item_id and item_id not in seen_keys:
                                seen_keys.add(item_id)
                                item["_discovery_source"] = "HuggingFace Models API"
                                item["_discovery_query"] = hf_url
                                yield item
                                yielded_count += 1
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"Error querying Hugging Face API for pipeline {pipeline}: {e}")

            # 3. Discover via GitHub Model Search if limit not reached
            if yielded_count < limit:
                gh_headers = dict(headers)
                gh_headers["Accept"] = "application/vnd.github.v3+json"
                if self.github_token:
                    gh_headers["Authorization"] = f"token {self.github_token}"

                queries = [
                    "topic:foundation-model stars:>5",
                    "topic:llm stars:>10",
                    "topic:vision-language-model stars:>5",
                    "topic:text-generation stars:>5",
                    "topic:diffusion-model stars:>5"
                ]

                for query in queries:
                    if yielded_count >= limit:
                        break
                    for page in range(1, 4):
                        if yielded_count >= limit:
                            break
                        gh_url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=30&page={page}"
                        try:
                            logger.info(f"Querying GitHub Model Search API: q='{query}' page={page}")
                            resp = await client.get(gh_url, headers=gh_headers)
                            if resp.status_code in (403, 429):
                                backoff = 5.0 + random.uniform(0.5, 2.0)
                                logger.warning(f"GitHub API rate limit. Backoff {backoff:.1f}s...")
                                await asyncio.sleep(backoff)
                                continue
                            if resp.status_code == 200:
                                data = resp.json()
                                items = data.get("items", [])
                                if not items:
                                    break
                                for item in items:
                                    if yielded_count >= limit:
                                        break
                                    item_id = item.get("full_name") or item.get("html_url")
                                    if item_id and item_id not in seen_keys:
                                        seen_keys.add(item_id)
                                        item["_discovery_source"] = "GitHub Model Search"
                                        item["_discovery_query"] = query
                                        yield item
                                        yielded_count += 1
                                await asyncio.sleep(1.0 + random.uniform(0.1, 0.4))
                            else:
                                break
                        except Exception as e:
                            logger.error(f"Error querying GitHub Model Search API: {e}")
                            break

        logger.info(f"ModelsAdapter finished discovery. Total candidates yielded: {yielded_count}")
