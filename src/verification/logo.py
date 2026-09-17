from urllib.parse import urljoin
from typing import Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
from src.utils.logging import setup_logger
from src.models.tool import VerificationResult

logger = setup_logger("logo_verifier")


class OfficialLogoVerifier:
    """
    Extracts official logo / favicon asset from verified official website metadata.
    Distinguishes between blocked access and missing logos.
    """

    def __init__(self, user_agent: str = None):
        self.user_agent = user_agent or "AI-Orbit-Ingestion-Bot/1.0 (+https://ai-orbit.org)"

    async def discover_logo(self, record: Dict[str, Any], verification_result: VerificationResult) -> Dict[str, Any]:
        """
        Extracts official logo URL. If HTTP access is blocked, flags logo_access_blocked.
        """
        url = record.get("url")
        
        # Base state
        record["logo_url"] = None
        record["logo_verified"] = False
        record["logo_found"] = False
        record["logo_access_blocked"] = False
        record["logo_source"] = None

        if not url:
            return record

        if verification_result.verification_status == "ACCESS_BLOCKED":
            record["logo_access_blocked"] = True
            logger.info(f"Skipping logo extraction for '{record.get('name')}' due to ACCESS_BLOCKED.")
            return record

        if not verification_result.accessible:
            return record

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=8.0,
                headers={"User-Agent": self.user_agent}
            ) as client:
                res = await client.get(url)
                if res.status_code in (403, 429, 401):
                    record["logo_access_blocked"] = True
                    return record
                elif res.status_code != 200:
                    return record

                soup = BeautifulSoup(res.text, "html.parser")
                
                logo_url: Optional[str] = None
                logo_source: Optional[str] = None

                # 1. Open Graph Image
                og_img = soup.find("meta", attrs={"property": "og:image"}) or \
                         soup.find("meta", attrs={"name": "og:image"})
                if og_img and og_img.get("content"):
                    raw_src = og_img.get("content").strip()
                    logo_url = urljoin(url, raw_src)
                    logo_source = "og:image"

                # 2. Apple Touch Icon
                if not logo_url:
                    apple_icon = soup.find("link", attrs={"rel": lambda r: r and "apple-touch-icon" in r.lower()})
                    if apple_icon and apple_icon.get("href"):
                        logo_url = urljoin(url, apple_icon.get("href").strip())
                        logo_source = "apple-touch-icon"

                # 3. Favicon
                if not logo_url:
                    icon_tag = soup.find("link", attrs={"rel": lambda r: r and "icon" in r.lower()})
                    if icon_tag and icon_tag.get("href"):
                        logo_url = urljoin(url, icon_tag.get("href").strip())
                        logo_source = "favicon"

                # 4. Fallback
                if not logo_url:
                    logo_url = urljoin(url, "/favicon.ico")
                    logo_source = "favicon_fallback"

                if logo_url:
                    record["logo_url"] = logo_url
                    record["logo_found"] = True
                    record["logo_source"] = logo_source
                    
                    # Do NOT mark GitHub social preview or githubassets images as verified official logos automatically
                    is_github_preview = any(domain in logo_url.lower() for domain in [
                        "githubassets.com", "githubusercontent.com", "github.com/og/", "github.com"
                    ]) or logo_source == "github_social_preview"

                    if is_github_preview or not record.get("official_url"):
                        record["logo_verified"] = False
                        if logo_source in ("og:image", None):
                            record["logo_source"] = "github_social_preview"
                        logger.info(f"Discovered fallback logo asset ({record['logo_source']}) for '{record.get('name')}': {logo_url}")
                    else:
                        record["logo_verified"] = True
                        logger.info(f"Discovered official logo ({logo_source}) for '{record.get('name')}': {logo_url}")

                return record

        except Exception as e:
            logger.warning(f"Failed logo discovery for '{record.get('name')}': {e}")
            return record
