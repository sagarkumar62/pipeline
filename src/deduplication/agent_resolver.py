from typing import Dict, List, Tuple, Any, Optional
from src.utils.logging import setup_logger
from src.utils.urls import normalize_url

logger = setup_logger("agent_resolver")


class AgentDeduplicationResolver:
    """
    Deterministic deduplication and entity resolution engine for Agent entities.
    
    Resolution Priority:
    1. Exact Registry ID / Stable Entity ID
    2. Normalized Repository URL match
    3. Canonical Official URL match
    4. Maintainer/Agent Name identity pair match
    5. Package identifier match (if available)
    """

    def __init__(self):
        self._seen_ids: Dict[str, Dict[str, Any]] = {}
        self._repo_url_map: Dict[str, str] = {}         # normalized repo url -> canonical_id
        self._official_url_map: Dict[str, str] = {}     # normalized official url -> canonical_id
        self._maintainer_name_map: Dict[str, str] = {}    # "maintainer/agent_name" -> canonical_id
        self._pkg_map: Dict[str, str] = {}              # package name -> canonical_id

    def _normalize_repo(self, repo_url: str) -> str:
        if not repo_url:
            return ""
        url = repo_url.lower().strip()
        url = url.replace("https://", "").replace("http://", "").replace("github.com/", "")
        if url.endswith(".git"):
            url = url[:-4]
        return url.strip("/")

    def load_baseline(self, records: List[Dict[str, Any]]) -> int:
        """Pre-loads existing Agent records into deduplication indexes."""
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

            official_url = rec.get("official_url")
            if official_url and "github.com" not in official_url.lower():
                norm_off = normalize_url(official_url)
                self._official_url_map[norm_off] = rec_id

            maintainer = (rec.get("maintainer") or "").lower().strip()
            name = (rec.get("name") or "").lower().strip()
            if maintainer and name:
                self._maintainer_name_map[f"{maintainer}/{name}"] = rec_id

            pkg = rec.get("package_name")
            if pkg:
                self._pkg_map[pkg.lower().strip()] = rec_id

            count += 1

        logger.info(f"Loaded {count} baseline Agent records into resolver indexes.")
        return count

    def resolve(self, record: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Resolves a candidate Agent record against existing indexed Agent entities.
        
        Returns:
            Tuple[resolved_record, is_duplicate]
        """
        rec_id = record.get("id")
        repo_url = record.get("repository_url") or record.get("url") or ""
        norm_url = normalize_url(repo_url) if repo_url else ""
        official_url = record.get("official_url") or ""
        norm_off = normalize_url(official_url) if (official_url and "github.com" not in official_url.lower()) else ""
        maintainer = (record.get("maintainer") or "").lower().strip()
        name = (record.get("name") or "").lower().strip()
        m_n_key = f"{maintainer}/{name}" if maintainer and name else ""
        pkg = (record.get("package_name") or "").lower().strip()

        # 1. Exact Stable ID Match
        if rec_id and rec_id in self._seen_ids:
            canonical = self._seen_ids[rec_id]
            record["duplicate_of"] = canonical["id"]
            record["match_method"] = "exact_stable_id"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate Agent found by exact ID: '{rec_id}'")
            return record, True

        # 2. Normalized Repository URL Match
        if norm_url and norm_url in self._repo_url_map:
            canonical_id = self._repo_url_map[norm_url]
            canonical = self._seen_ids[canonical_id]
            record["duplicate_of"] = canonical_id
            record["match_method"] = "exact_repository_url"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate Agent found by repository URL: '{norm_url}'")
            return record, True

        # 3. Canonical Official Website Match
        if norm_off and norm_off in self._official_url_map:
            canonical_id = self._official_url_map[norm_off]
            canonical = self._seen_ids[canonical_id]
            record["duplicate_of"] = canonical_id
            record["match_method"] = "exact_official_url"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate Agent found by official URL: '{norm_off}'")
            return record, True

        # 4. Canonical Maintainer/Name Pair Match
        if m_n_key and m_n_key in self._maintainer_name_map:
            canonical_id = self._maintainer_name_map[m_n_key]
            canonical = self._seen_ids[canonical_id]
            record["duplicate_of"] = canonical_id
            record["match_method"] = "maintainer_name_identity_match"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate Agent found by maintainer/name pair: '{m_n_key}'")
            return record, True

        # 5. Package Identifier Match
        if pkg and pkg in self._pkg_map:
            canonical_id = self._pkg_map[pkg]
            canonical = self._seen_ids[canonical_id]
            record["duplicate_of"] = canonical_id
            record["match_method"] = "exact_package_identifier"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate Agent found by package identifier: '{pkg}'")
            return record, True

        # Register as new canonical entity
        self._seen_ids[rec_id] = record
        if norm_url:
            self._repo_url_map[norm_url] = rec_id
        if norm_off:
            self._official_url_map[norm_off] = rec_id
        if m_n_key:
            self._maintainer_name_map[m_n_key] = rec_id
        if pkg:
            self._pkg_map[pkg] = rec_id

        record["duplicate_of"] = None
        record["match_method"] = None
        record["match_confidence"] = None
        record["is_baseline_match"] = False
        return record, False
