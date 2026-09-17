import asyncio
import re
from datetime import datetime, timezone
from typing import Dict, Any, List
import httpx
from bs4 import BeautifulSoup
from src.utils.logging import setup_logger
from src.utils.urls import extract_domain, normalize_url
from src.models.tool import VerificationResult, VerificationEvidence

logger = setup_logger("website_verifier")


class OfficialWebsiteVerifier:
    """
    Verifies official website URLs via HTTP checks, content title/meta verification,
    and domain identity checks. Separates accessibility from identity verification.
    """

    def __init__(self, timeout_seconds: float = 10.0, user_agent: str = None):
        self.timeout = timeout_seconds
        self.user_agent = user_agent or "AI-Orbit-Ingestion-Bot/1.0 (+https://ai-orbit.org)"

    async def verify_website(self, record: Dict[str, Any]) -> VerificationResult:
        """
        Asynchronously verifies the record's URL and builds a comprehensive VerificationResult.
        """
        url = record.get("url")
        tool_name = record.get("name", "")
        source_url = record.get("source_url", "")
        source_name = record.get("source_name", "UNKNOWN")
        
        result = VerificationResult()

        if not url:
            result.verification_status = "NOT_FOUND"
            result.reason = "Missing official URL"
            return result

        target_domain = extract_domain(url)
        
        # 1. Base Domain Identity Evidence
        if source_url and extract_domain(source_url) == target_domain:
            result.evidence.append(VerificationEvidence(
                type="DOMAIN_MATCH",
                source=source_name,
                value=f"Source URL domain matches target domain: {target_domain}",
                result=True
            ))
            result.official_domain_match = True
        
        # If the source is a highly trusted seed, treat it as a strong identity claim
        if source_name == "Official AI Directory Seed":
            result.evidence.append(VerificationEvidence(
                type="SOURCE_CLAIM",
                source=source_name,
                value=f"Trusted seed asserts domain is {target_domain}",
                result=True
            ))
            result.official_domain_match = True

        headers = {"User-Agent": self.user_agent}

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=self.timeout,
                headers=headers
            ) as client:
                response = await client.get(url)
                result.http_status = response.status_code
                
                # Check for Access Blocked
                if response.status_code in (403, 429, 401):
                    result.accessible = False
                    result.verification_status = "ACCESS_BLOCKED"
                    result.reason = f"HTTP {response.status_code}: Anti-bot or rate limit"
                    result.evidence.append(VerificationEvidence(
                        type="HTTP_RESPONSE",
                        source="HTTP Client",
                        value=f"Status {response.status_code}",
                        result=False
                    ))
                    # Identity is still verifiable via secondary evidence (handled by validator)
                    return result

                if response.status_code != 200:
                    result.accessible = False
                    result.verification_status = "SERVER_ERROR" if response.status_code >= 500 else "NOT_FOUND"
                    result.reason = f"HTTP Status {response.status_code}"
                    return result

                # HTTP 200 OK
                result.accessible = True
                final_url = str(response.url)
                final_domain = extract_domain(final_url)
                result.canonical_domain = final_domain
                
                if final_domain != target_domain:
                    result.redirect_verified = True
                    result.evidence.append(VerificationEvidence(
                        type="REDIRECT",
                        source="HTTP Client",
                        value=f"Redirected from {target_domain} to {final_domain}",
                        result=True
                    ))

                # Parse HTML content
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Extract Page Title
                title_tag = soup.find("title")
                page_title = title_tag.get_text(strip=True) if title_tag else ""
                result.page_title = page_title
                
                # Extract Meta Description
                meta_desc_tag = soup.find("meta", attrs={"name": "description"}) or \
                                soup.find("meta", attrs={"property": "og:description"})
                meta_desc = meta_desc_tag.get("content", "").strip() if meta_desc_tag else ""
                result.meta_description = meta_desc

                # Identity relevance check
                name_tokens = [t.lower() for t in re.findall(r"\w+", tool_name) if len(t) > 2]
                page_text_sample = (page_title + " " + meta_desc + " " + final_domain).lower()

                relevant = any(token in page_text_sample for token in name_tokens) or len(name_tokens) == 0
                
                if relevant:
                    result.title_match = True
                    result.content_match = True
                    result.verification_status = "ACCESSIBLE_VERIFIED"
                    result.reason = f"HTTP 200 OK | Domain: {final_domain} | Title matched"
                    result.evidence.append(VerificationEvidence(
                        type="PAGE_TITLE",
                        source="HTTP Client",
                        value=page_title[:100],
                        result=True
                    ))
                    logger.info(f"Verified official site for '{tool_name}' ({final_url})")
                else:
                    result.title_match = False
                    result.verification_status = "IDENTITY_MISMATCH"
                    result.reason = f"HTTP 200 OK, but domain/title content mismatched: '{page_title[:40]}'"
                    result.evidence.append(VerificationEvidence(
                        type="PAGE_TITLE",
                        source="HTTP Client",
                        value=page_title[:100],
                        result=False
                    ))
                    logger.warning(f"Domain/content mismatch for '{tool_name}' at {final_url}")

                return result

        except httpx.TimeoutException:
            result.accessible = False
            result.verification_status = "TIMEOUT"
            result.reason = f"Connection timeout after {self.timeout}s"
            logger.warning(f"Timeout verifying website for '{tool_name}': {url}")
            return result

        except Exception as e:
            result.accessible = False
            result.verification_status = "DNS_FAILURE" if "NameResolutionError" in str(type(e)) else "UNKNOWN"
            result.reason = f"Network or SSL error: {str(e)[:100]}"
            logger.warning(f"Error verifying website for '{tool_name}': {e}")
            return result
