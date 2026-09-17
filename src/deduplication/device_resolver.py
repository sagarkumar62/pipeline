from typing import Dict, List, Tuple, Any, Optional
from src.utils.logging import setup_logger
from src.utils.urls import normalize_url

logger = setup_logger("device_resolver")


class DeviceDeduplicationResolver:
    """
    Deterministic deduplication and entity resolution engine for Device entities.
    
    Enforces distinct identity rules:
    - Distinct device generations or models (e.g., Jetson Orin Nano vs Jetson Orin AGX) remain distinct canonical models.
    - Resolution requires exact manufacturer + device product identity or exact URL matching.
    
    Resolution Priority:
    1. Exact Registry ID / Stable Entity ID
    2. Normalized Repository URL match
    3. Canonical Official Product URL match
    4. Manufacturer/Device Name identity pair match
    """

    def __init__(self):
        self._seen_ids: Dict[str, Dict[str, Any]] = {}
        self._repo_url_map: Dict[str, str] = {}         # normalized repo url -> canonical_id
        self._official_url_map: Dict[str, str] = {}     # normalized official url -> canonical_id
        self._mfg_name_map: Dict[str, str] = {}         # "manufacturer/device_name" -> canonical_id

    def _normalize_repo(self, repo_url: str) -> str:
        if not repo_url:
            return ""
        url = repo_url.lower().strip()
        url = url.replace("https://", "").replace("http://", "").replace("github.com/", "")
        if url.endswith(".git"):
            url = url[:-4]
        return url.strip("/")

    def load_baseline(self, records: List[Dict[str, Any]]) -> int:
        """Pre-loads existing Device records into deduplication indexes."""
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

            mfg = (rec.get("manufacturer") or "").lower().strip()
            name = (rec.get("name") or "").lower().strip()
            if mfg and name:
                self._mfg_name_map[f"{mfg}/{name}"] = rec_id

            count += 1

        logger.info(f"Loaded {count} baseline Device records into resolver indexes.")
        return count

    def resolve(self, record: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Resolves a candidate Device record against existing indexed Device entities.
        
        Returns:
            Tuple[resolved_record, is_duplicate]
        """
        rec_id = record.get("id")
        repo_url = record.get("repository_url") or record.get("url") or ""
        norm_url = normalize_url(repo_url) if repo_url else ""
        official_url = record.get("official_url") or ""
        norm_off = normalize_url(official_url) if (official_url and "github.com" not in official_url.lower()) else ""
        mfg = (record.get("manufacturer") or "").lower().strip()
        name = (record.get("name") or "").lower().strip()
        mfg_name_key = f"{mfg}/{name}" if mfg and name else ""

        # 1. Exact Stable ID Match
        if rec_id and rec_id in self._seen_ids:
            canonical = self._seen_ids[rec_id]
            record["duplicate_of"] = canonical["id"]
            record["match_method"] = "exact_stable_id"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate Device found by exact ID: '{rec_id}'")
            return record, True

        # 2. Normalized Repository URL Match
        if norm_url and norm_url in self._repo_url_map:
            canonical_id = self._repo_url_map[norm_url]
            canonical = self._seen_ids[canonical_id]
            record["duplicate_of"] = canonical_id
            record["match_method"] = "exact_repository_url"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate Device found by repository URL: '{norm_url}'")
            return record, True

        # 3. Canonical Official Product URL Match
        if norm_off and norm_off in self._official_url_map:
            canonical_id = self._official_url_map[norm_off]
            canonical = self._seen_ids[canonical_id]
            record["duplicate_of"] = canonical_id
            record["match_method"] = "exact_official_url"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate Device found by official URL: '{norm_off}'")
            return record, True

        # 4. Manufacturer/Name Identity Pair Match
        if mfg_name_key and mfg_name_key in self._mfg_name_map:
            canonical_id = self._mfg_name_map[mfg_name_key]
            canonical = self._seen_ids[canonical_id]
            record["duplicate_of"] = canonical_id
            record["match_method"] = "manufacturer_name_identity_match"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate Device found by manufacturer/name pair: '{mfg_name_key}'")
            return record, True

        # Register as new canonical entity
        self._seen_ids[rec_id] = record
        if norm_url:
            self._repo_url_map[norm_url] = rec_id
        if norm_off:
            self._official_url_map[norm_off] = rec_id
        if mfg_name_key:
            self._mfg_name_map[mfg_name_key] = rec_id

        record["duplicate_of"] = None
        record["match_method"] = None
        record["match_confidence"] = None
        record["is_baseline_match"] = False
        return record, False
