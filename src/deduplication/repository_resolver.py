from typing import Dict, List, Tuple, Any, Optional
from rapidfuzz import fuzz
from src.utils.logging import setup_logger
from src.utils.urls import normalize_url

logger = setup_logger("repository_resolver")


class RepositoryDeduplicationResolver:
    """
    Deterministic deduplication and entity resolution engine for Repository entities.
    
    Resolution Hierarchy:
    1. Exact Stable ID (`repository:<owner>/<name>`)
    2. Normalized Repository URL match (`https://github.com/owner/name`)
    3. Canonical Owner/Name identity pair match
    4. Blocked candidate comparison (Same owner + normalized name)
    """

    def __init__(self, fuzzy_threshold: float = 95.0):
        self.fuzzy_threshold = fuzzy_threshold
        self._seen_ids: Dict[str, Dict[str, Any]] = {}
        self._url_map: Dict[str, str] = {}  # normalized_url -> canonical_id
        self._owner_repo_map: Dict[str, str] = {}  # "owner/name" -> canonical_id

    def load_baseline(self, records: List[Dict[str, Any]]) -> int:
        """Pre-loads existing repository records into deduplication indexes."""
        count = 0
        for r in records:
            rec = dict(r) if isinstance(r, dict) else r.model_dump()
            rec_id = rec.get("id")
            if not rec_id:
                continue

            self._seen_ids[rec_id] = rec

            url = rec.get("repository_url") or rec.get("url")
            if url:
                norm_url = normalize_url(url)
                self._url_map[norm_url] = rec_id

            owner = (rec.get("owner") or "").lower().strip()
            name = (rec.get("name") or "").lower().strip()
            if owner and name:
                self._owner_repo_map[f"{owner}/{name}"] = rec_id

            count += 1

        logger.info(f"Loaded {count} baseline repository records into resolver indexes.")
        return count

    def resolve(self, record: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Resolves a candidate repository against existing indexed repositories.
        
        Returns:
            Tuple[resolved_record, is_duplicate]
        """
        rec_id = record.get("id")
        owner = (record.get("owner") or "").lower().strip()
        name = (record.get("name") or "").lower().strip()
        repo_url = record.get("repository_url") or record.get("url") or ""
        norm_url = normalize_url(repo_url)

        owner_repo_key = f"{owner}/{name}" if owner and name else ""

        # 1. Exact Stable ID Match
        if rec_id and rec_id in self._seen_ids:
            canonical = self._seen_ids[rec_id]
            record["duplicate_of"] = canonical["id"]
            record["match_method"] = "exact_stable_id"
            record["match_confidence"] = 1.0
            logger.info(f"Duplicate repo found by exact ID: '{owner_repo_key}' -> '{canonical['id']}'")
            return record, True

        # 2. Normalized Repository URL Match
        if norm_url and norm_url in self._url_map:
            canonical_id = self._url_map[norm_url]
            canonical = self._seen_ids[canonical_id]
            record["duplicate_of"] = canonical_id
            record["match_method"] = "exact_repository_url"
            record["match_confidence"] = 1.0
            logger.info(f"Duplicate repo found by repository URL: '{norm_url}'")
            return record, True

        # 3. Canonical Owner/Name Identity Pair Match
        if owner_repo_key and owner_repo_key in self._owner_repo_map:
            canonical_id = self._owner_repo_map[owner_repo_key]
            canonical = self._seen_ids[canonical_id]
            record["duplicate_of"] = canonical_id
            record["match_method"] = "owner_repo_identity_match"
            record["match_confidence"] = 1.0
            logger.info(f"Duplicate repo found by owner/name pair: '{owner_repo_key}'")
            return record, True

        # 4. Strict Non-Match Safety: Same name under DIFFERENT owners are NOT duplicates!
        # (e.g., 'facebook/react' vs 'google/react' are different repos)

        # Register as new canonical entity
        self._seen_ids[rec_id] = record
        if norm_url:
            self._url_map[norm_url] = rec_id
        if owner_repo_key:
            self._owner_repo_map[owner_repo_key] = rec_id

        record["duplicate_of"] = None
        record["match_method"] = None
        record["match_confidence"] = None
        return record, False
