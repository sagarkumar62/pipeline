from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import re
from typing import Optional

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "msclkid", "ref", "source", "_hsenc", "_hsmi", "mc_cid", "mc_eid"
}


def normalize_url(url: str) -> str:
    """
    Normalizes a URL deterministically.
    - Ensures scheme (default https)
    - Lowercases scheme and host
    - Strips 'www.' prefix for domain consistency
    - Removes trailing slashes on paths
    - Removes URL fragments
    - Removes common tracking query parameters
    """
    if not url or not isinstance(url, str):
        return ""

    url = url.strip()
    url_lower = url.lower()
    if url_lower.startswith("internal://"):
        return url

    if not (url_lower.startswith("http://") or url_lower.startswith("https://")):
        url = "https://" + url

    parsed = urlparse(url)
    
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    
    # Remove port if default
    if (scheme == "http" and netloc.endswith(":80")) or (scheme == "https" and netloc.endswith(":443")):
        netloc = netloc.rsplit(":", 1)[0]

    # Normalize www.
    if netloc.startswith("www."):
        netloc = netloc[4:]

    # Path normalization: strip trailing slash for all paths including root '/'
    path = parsed.path
    if path and path.endswith("/"):
        path = path.rstrip("/")

    # Strip tracking query params
    query_params = parse_qs(parsed.query, keep_blank_values=False)
    filtered_params = {
        k: v for k, v in query_params.items() if k.lower() not in TRACKING_PARAMS
    }
    
    # Reconstruct query string deterministically (sorted keys)
    new_query = urlencode(filtered_params, doseq=True) if filtered_params else ""

    # Fragment is stripped for canonical URL identity
    fragment = ""

    normalized = urlunparse((scheme, netloc, path, parsed.params, new_query, fragment))
    return normalized


def extract_domain(url: str) -> Optional[str]:
    """
    Extracts canonical domain (e.g. 'openai.com') from a normalized or raw URL.
    """
    if not url:
        return None
    normalized = normalize_url(url)
    parsed = urlparse(normalized)
    return parsed.netloc if parsed.netloc else None
