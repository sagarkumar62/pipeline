import re
from typing import Dict, List, Tuple, Any, Optional
from src.utils.logging import setup_logger
from src.utils.urls import normalize_url, extract_domain

logger = setup_logger("company_resolver")


class CompanyDeduplicationResolver:
    """
    Deterministic deduplication and entity resolution engine for Company entities.
    
    Resolution Priority:
    1. Exact Registry ID / Stable Entity ID
    2. Canonical Official Domain match (e.g. openai.com, anthropic.com)
    3. Exact GitHub Organization URL match
    4. Exact Legal / Company Name Normalization match
    """

    def __init__(self):
        self._seen_ids: Dict[str, Dict[str, Any]] = {}
        self._domain_map: Dict[str, str] = {}           # clean_domain -> canonical_id
        self._github_url_map: Dict[str, str] = {}       # github_url -> canonical_id
        self._name_map: Dict[str, str] = {}             # normalized_name -> canonical_id

    def load_baseline(self, records: List[Dict[str, Any]]) -> int:
        """Pre-loads existing Company records into deduplication indexes."""
        count = 0
        for r in records:
            rec = dict(r) if isinstance(r, dict) else r.model_dump()
            rec_id = rec.get("id")
            if not rec_id:
                continue

            rec["is_baseline"] = True
            self._seen_ids[rec_id] = rec

            off_url = rec.get("official_url") or rec.get("url")
            if off_url and "github.com" not in off_url.lower():
                domain = extract_domain(off_url).lower().replace("www.", "")
                if domain:
                    self._domain_map[domain] = rec_id

            gh_url = rec.get("github_url")
            if gh_url:
                norm_gh = normalize_url(gh_url)
                self._github_url_map[norm_gh] = rec_id

            name = (rec.get("name") or rec.get("company_name") or "").lower().strip()
            norm_name = self._normalize_company_name(name)
            if norm_name:
                self._name_map[norm_name] = rec_id

            count += 1

        logger.info(f"Loaded {count} baseline Company records into resolver indexes.")
        return count

    def _normalize_company_name(self, name: str) -> str:
        """Normalizes company name by removing legal suffixes while preserving distinct identities."""
        clean = re.sub(r"[,.]", "", name.lower().strip())
        # Remove common legal suffixes
        clean = re.sub(r"\b(inc|llc|ltd|corp|corporation|gmbh|sa|pvt)\b", "", clean).strip()
        clean = re.sub(r"\s+", " ", clean)
        return clean

    def resolve(self, record: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Resolves a candidate Company record against existing indexed Company entities.
        
        Returns:
            Tuple[resolved_record, is_duplicate]
        """
        rec_id = record.get("id")
        off_url = record.get("official_url") or record.get("url") or ""
        domain = extract_domain(off_url).lower().replace("www.", "") if (off_url and "github.com" not in off_url.lower()) else ""
        gh_url = record.get("github_url") or ""
        norm_gh = normalize_url(gh_url) if gh_url else ""
        name = (record.get("name") or record.get("company_name") or "").lower().strip()
        norm_name = self._normalize_company_name(name)

        # 1. Exact Stable ID Match
        if rec_id and rec_id in self._seen_ids:
            canonical = self._seen_ids[rec_id]
            record["duplicate_of"] = canonical["id"]
            record["match_method"] = "exact_stable_id"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate Company found by exact ID: '{rec_id}'")
            return record, True

        # 2. Canonical Official Domain Match
        if domain and domain in self._domain_map:
            canonical_id = self._domain_map[domain]
            canonical = self._seen_ids[canonical_id]
            record["duplicate_of"] = canonical_id
            record["match_method"] = "exact_official_domain"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate Company found by official domain: '{domain}'")
            return record, True

        # 3. Exact GitHub Organization URL Match
        if norm_gh and norm_gh in self._github_url_map:
            canonical_id = self._github_url_map[norm_gh]
            canonical = self._seen_ids[canonical_id]
            record["duplicate_of"] = canonical_id
            record["match_method"] = "exact_github_url"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate Company found by GitHub URL: '{norm_gh}'")
            return record, True

        # 4. Exact Normalized Name Match
        if norm_name and norm_name in self._name_map:
            canonical_id = self._name_map[norm_name]
            canonical = self._seen_ids[canonical_id]
            record["duplicate_of"] = canonical_id
            record["match_method"] = "exact_normalized_company_name"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical.get("is_baseline", False)
            logger.info(f"Duplicate Company found by normalized name: '{norm_name}'")
            return record, True

        # Register as new canonical entity
        self._seen_ids[rec_id] = record
        if domain:
            self._domain_map[domain] = rec_id
        if norm_gh:
            self._github_url_map[norm_gh] = rec_id
        if norm_name:
            self._name_map[norm_name] = rec_id

        record["duplicate_of"] = None
        record["match_method"] = None
        record["match_confidence"] = None
        record["is_baseline_match"] = False
        return record, False
