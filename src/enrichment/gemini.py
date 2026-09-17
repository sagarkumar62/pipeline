"""
Phase 4 Gemini API Provider

Google Gemini API implementation supporting evidence-based description generation,
structured JSON response parsing, rate-limit backoff, and auth failure tracking.
"""

import os
import re
import json
import time
import asyncio
from typing import Optional
import httpx
from src.enrichment.llm_base import BaseLLMProvider
from src.enrichment.schema import EvidencePackage, LLMResult, StructuredLLMOutput
from src.utils.logging import setup_logger

logger = setup_logger("gemini_provider")


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API Provider implementation."""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

    @property
    def provider_name(self) -> str:
        return "Gemini"

    @property
    def is_available(self) -> bool:
        return bool(self.api_key) and not self.auth_failed

    async def generate_description(self, evidence: EvidencePackage) -> LLMResult:
        if not self.is_available:
            return LLMResult(
                provider_name=self.provider_name,
                status="FALLBACK",
                error_message="Gemini API key not configured or auth failed",
            )

        start_time = time.time()
        
        prompt = (
            f"You are a strict factual technical data editor for AI Orbit.\n"
            f"Task: Write a 1-2 sentence description for the tool '{evidence.tool_name}' strictly based on the evidence below.\n\n"
            f"STRICT RULES:\n"
            f"1. Explain what the Tool does specifically using ONLY supplied evidence.\n"
            f"2. Do NOT use your pretrained knowledge to fill missing facts.\n"
            f"3. Avoid marketing language, superlatives, pricing claims, customer claims, performance claims, founder claims, or dates unless explicitly present.\n"
            f"4. Output MUST be valid JSON adhering strictly to this schema:\n"
            f'{{\n  "description": "...",\n  "grounded": true,\n  "confidence": "high",\n  "evidence_used": [{{"source_url": "...", "source_type": "..."}}]\n}}\n'
            f"5. If evidence is insufficient, output: {{\n  \"description\": null,\n  \"grounded\": false,\n  \"confidence\": \"low\",\n  \"evidence_used\": []\n}}\n\n"
            f"SUPPLIED EVIDENCE:\n"
            f"- Tool Name: {evidence.tool_name}\n"
            f"- Repository Description: {evidence.repository_description or 'None'}\n"
            f"- Official Website URL: {evidence.official_website_url or 'None'}\n"
            f"- Official Website Content: {evidence.official_website_content or 'None'}\n"
            f"- GitHub Repo URL: {evidence.github_repo_url or 'None'}\n"
            f"- Topics: {', '.join(evidence.topics)}\n"
            f"- README Excerpt: {evidence.readme_excerpt or 'None'}\n"
            f"- Available Source URLs: {json.dumps(evidence.source_urls)}\n"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 250,
                "responseMimeType": "application/json"
            }
        }

        url = f"{self.endpoint}?key={self.api_key}"
        retries = 2

        for attempt in range(1, retries + 2):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.post(url, json=payload)
                    latency = (time.time() - start_time) * 1000.0

                    if res.status_code in (401, 403):
                        self.auth_failed = True
                        logger.error(f"Gemini API Auth Failure HTTP {res.status_code}. Marking provider unavailable.")
                        return LLMResult(
                            provider_name=self.provider_name,
                            status="AUTH_ERROR",
                            error_message=f"HTTP {res.status_code} Unauthorized",
                            latency_ms=latency,
                        )
                    elif res.status_code == 429:
                        logger.warning(f"Gemini API 429 Rate Limited (attempt {attempt}).")
                        if attempt <= retries:
                            retry_after = float(res.headers.get("Retry-After", 2.0 * attempt))
                            await asyncio.sleep(retry_after)
                            continue
                        return LLMResult(
                            provider_name=self.provider_name,
                            status="RATE_LIMITED",
                            error_message="HTTP 429 Rate Limit Exceeded",
                            latency_ms=latency,
                        )
                    elif res.status_code == 200:
                        data = res.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                            clean_text = raw_text
                            if "```" in clean_text:
                                match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', clean_text)
                                if match:
                                    clean_text = match.group(1).strip()
                            else:
                                match = re.search(r'(\{[\s\S]*\})', clean_text)
                                if match:
                                    clean_text = match.group(1).strip()
                            try:
                                json_data = json.loads(clean_text)
                                structured = StructuredLLMOutput(**json_data)
                                for ev in structured.evidence_used:
                                    if ev.source_url:
                                        ev.source_url = re.sub(r'^(https?://)+', 'https://', ev.source_url)
                                return LLMResult(
                                    description=structured.description,
                                    grounded=structured.grounded,
                                    confidence=structured.confidence,
                                    evidence_used=[e.model_dump() for e in structured.evidence_used],
                                    provider_name=self.provider_name,
                                    status="SUCCESS" if structured.grounded and structured.description else "UNGROUNDED",
                                    latency_ms=latency,
                                )
                            except Exception as parse_err:
                                logger.warning(f"Gemini API JSON parse error: {parse_err}. Raw text: {raw_text[:100]}")
                                return LLMResult(
                                    provider_name=self.provider_name,
                                    status="MALFORMED",
                                    error_message=f"JSON parse error: {parse_err}",
                                    latency_ms=latency,
                                )
                    else:
                        logger.warning(f"Gemini API HTTP {res.status_code}: {res.text}")
                        if attempt <= retries:
                            await asyncio.sleep(1.0 * attempt)
                            continue
                        return LLMResult(
                            provider_name=self.provider_name,
                            status="ERROR",
                            error_message=f"HTTP {res.status_code}",
                            latency_ms=latency,
                        )

            except httpx.TimeoutException:
                latency = (time.time() - start_time) * 1000.0
                logger.warning(f"Gemini API Timeout (attempt {attempt}).")
                if attempt <= retries:
                    await asyncio.sleep(1.0 * attempt)
                    continue
                return LLMResult(
                    provider_name=self.provider_name,
                    status="TIMEOUT",
                    error_message="HTTP Connection Timeout",
                    latency_ms=latency,
                )
            except Exception as e:
                latency = (time.time() - start_time) * 1000.0
                logger.warning(f"Gemini API Exception: {e}")
                return LLMResult(
                    provider_name=self.provider_name,
                    status="ERROR",
                    error_message=str(e),
                    latency_ms=latency,
                )

        return LLMResult(
            provider_name=self.provider_name,
            status="FALLBACK",
            error_message="All retries exhausted",
        )
