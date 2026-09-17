from typing import Dict, List, Tuple, Any, Optional
from src.utils.logging import setup_logger
from src.utils.urls import normalize_url

logger = setup_logger("mcp_resolver")


class MCPDeduplicationResolver:
    """
    Deterministic deduplication and entity resolution engine for MCP entities.
    
    Resolution Priority:
    1. Exact Registry ID / Stable Entity ID
    2. Normalized Repository URL match
    3. Package identifier + ecosystem match (e.g., npm / pypi package name)
    4. Canonical Maintainer/Server Name identity pair match
    """

    def __init__(self):
        self._seen_ids: Dict[str, Dict[str, Any]] = {}
        self._repo_url_map: Dict[str, str] = {}      # normalized repo url -> canonical_id
        self._pkg_map: Dict[str, str] = {}           # "ecosystem:pkg_name" -> canonical_id
        self._maintainer_name_map: Dict[str, str] = {} # "maintainer/server_name" -> canonical_id

    def _normalize_repo(self, repo_url: str) -> str:
        if not repo_url:
            return ""
        url = repo_url.lower().strip()
        url = url.replace("https://", "").replace("http://", "").replace("github.com/", "")
        if url.endswith(".git"):
            url = url[:-4]
        return url.strip("/")

    def load_baseline(self, records: List[Dict[str, Any]]) -> int:
        """Pre-loads existing MCP records into deduplication indexes."""
        count = 0
        for r in records:
            rec = dict(r) if isinstance(r, dict) else r.model_dump()
            rec_id = rec.get("id")
            if not rec_id:
                continue

            rec["is_baseline"] = True
            self._seen_ids[rec_id] = rec

            repo_url = rec.get("repository_url") or rec.get("url")
            if repo_url:
                norm_url = normalize_url(repo_url)
                self._repo_url_map[norm_url] = rec_id

            pkg = rec.get("package_name") or rec.get("npm_package") or rec.get("pypi_package")
            if pkg:
                self._pkg_map[pkg.lower().strip()] = rec_id

            maintainer = (rec.get("maintainer") or "").lower().strip()
            name = (rec.get("name") or rec.get("server_name") or "").lower().strip()
            if maintainer and name:
                self._maintainer_name_map[f"{maintainer}/{name}"] = rec_id

            count += 1

        logger.info(f"Loaded {count} baseline MCP records into resolver indexes.")
        return count

    def resolve(self, record: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Resolves a candidate MCP record against existing indexed MCP entities.
        
        Returns:
            Tuple[resolved_record, is_duplicate]
        """
        rec_id = record.get("id")
        repo_url = record.get("repository_url") or record.get("url") or ""
        norm_url = normalize_url(repo_url) if repo_url else ""
        pkg = (record.get("package_name") or record.get("npm_package") or record.get("pypi_package") or "").lower().strip()
        maintainer = (record.get("maintainer") or "").lower().strip()
        name = (record.get("name") or record.get("server_name") or "").lower().strip()
        m_n_key = f"{maintainer}/{name}" if maintainer and name else ""

        # 1. Exact Stable ID Match
        if rec_id and rec_id in self._seen_ids:
            canonical = self._seen_ids[rec_id]
            record["duplicate_of"] = canonical["id"]
            record["match_method"] = "exact_stable_id"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate MCP found by exact ID: '{rec_id}'")
            return record, True

        # 2. Normalized Repository URL Match
        if norm_url and norm_url in self._repo_url_map:
            canonical_id = self._repo_url_map[norm_url]
            canonical = self._seen_ids[canonical_id]
            record["duplicate_of"] = canonical_id
            record["match_method"] = "exact_repository_url"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate MCP found by repository URL: '{norm_url}'")
            return record, True

        # 3. Package Identifier Match
        if pkg and pkg in self._pkg_map:
            canonical_id = self._pkg_map[pkg]
            canonical = self._seen_ids[canonical_id]
            record["duplicate_of"] = canonical_id
            record["match_method"] = "exact_package_identifier"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate MCP found by package identifier: '{pkg}'")
            return record, True

        # 4. Canonical Maintainer/Name Pair Match
        if m_n_key and m_n_key in self._maintainer_name_map:
            canonical_id = self._maintainer_name_map[m_n_key]
            canonical = self._seen_ids[canonical_id]
            record["duplicate_of"] = canonical_id
            record["match_method"] = "maintainer_name_identity_match"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate MCP found by maintainer/name pair: '{m_n_key}'")
            return record, True

        # Register as new canonical entity
        self._seen_ids[rec_id] = record
        if norm_url:
            self._repo_url_map[norm_url] = rec_id
        if pkg:
            self._pkg_map[pkg] = rec_id
        if m_n_key:
            self._maintainer_name_map[m_n_key] = rec_id

        record["duplicate_of"] = None
        record["match_method"] = None
        record["match_confidence"] = None
        record["is_baseline_match"] = False
        return record, False
