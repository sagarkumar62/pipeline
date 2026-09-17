import hashlib
from typing import Optional


def generate_tool_id(canonical_domain: Optional[str], normalized_name: str) -> str:
    """
    Generates a stable, deterministic canonical ID for a Tool.
    
    Formula:
    SHA256(canonical_domain:normalized_name) prefixed with 'tool_'
    
    If domain is missing or unverified, fallback to SHA256(normalized_name).
    """
    clean_domain = (canonical_domain or "").strip().lower()
    clean_name = normalized_name.strip().lower()
    
    raw_key = f"{clean_domain}:{clean_name}" if clean_domain else clean_name
    digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]
    return f"tool_{digest}"
