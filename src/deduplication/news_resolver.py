import re
import hashlib
from typing import Dict, List, Any, Tuple, Optional, Set
from src.models.news import NewsRecord
from src.utils.logging import setup_logger

logger = setup_logger("news_resolver")


class NewsDeduplicationResolver:
    """
    Deterministic entity resolution engine for News articles.
    Prevents duplicate reporting of the exact same article from the same publisher feed or URL.
    """

    def __init__(self):
        self.seen_url_hashes: Dict[str, str] = {}  # url_hash -> entity_id
        self.seen_content_hashes: Dict[str, str] = {}  # content_hash -> entity_id
        self.seen_title_domain_pairs: Dict[Tuple[str, str], str] = {}  # (domain, norm_title) -> entity_id

    @staticmethod
    def normalize_title_for_dedup(title: str) -> str:
        """Normalizes headline string for title-level exact match deduplication."""
        if not title:
            return ""
        norm = title.lower()
        norm = re.sub(r"[^\w\s]", "", norm)
        return re.sub(r"\s+", " ", norm).strip()

    def resolve(self, candidate: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Resolves whether a candidate News article is unique or a duplicate.
        Returns Tuple[resolved_candidate, is_duplicate].
        """
        cand_id = candidate.get("id")
        canonical_url = candidate.get("canonical_url") or candidate.get("url") or ""
        url_hash = candidate.get("canonical_url_hash") or NewsRecord.compute_canonical_url_hash(canonical_url)
        
        raw_title = candidate.get("canonical_title") or candidate.get("title") or ""
        norm_title = self.normalize_title_for_dedup(raw_title)
        domain = (candidate.get("source_domain") or "").lower()
        
        summary = candidate.get("summary") or ""
        content_hash = candidate.get("content_hash") or NewsRecord.compute_content_hash(raw_title, summary[:200])

        # -------------------------------------------------------------
        # 1. Exact Canonical URL Hash Match
        # -------------------------------------------------------------
        if url_hash in self.seen_url_hashes:
            dup_id = self.seen_url_hashes[url_hash]
            candidate["duplicate_of"] = dup_id
            candidate["duplicate_reason"] = f"Exact canonical URL hash match with '{dup_id}'"
            logger.info(f"Duplicate article found by URL hash: {cand_id} -> {dup_id}")
            return candidate, True

        # -------------------------------------------------------------
        # 2. Exact Publisher Domain + Normalized Title Pair Match
        # -------------------------------------------------------------
        title_pair = (domain, norm_title)
        if domain and norm_title and title_pair in self.seen_title_domain_pairs:
            dup_id = self.seen_title_domain_pairs[title_pair]
            candidate["duplicate_of"] = dup_id
            candidate["duplicate_reason"] = f"Exact publisher domain + normalized title match with '{dup_id}'"
            logger.info(f"Duplicate article found by domain+title pair: {cand_id} -> {dup_id}")
            return candidate, True

        # -------------------------------------------------------------
        # 3. Exact Content Hash Match
        # -------------------------------------------------------------
        if content_hash in self.seen_content_hashes:
            dup_id = self.seen_content_hashes[content_hash]
            candidate["duplicate_of"] = dup_id
            candidate["duplicate_reason"] = f"Exact content fingerprint match with '{dup_id}'"
            logger.info(f"Duplicate article found by content hash: {cand_id} -> {dup_id}")
            return candidate, True

        # Candidate is UNIQUE
        self.seen_url_hashes[url_hash] = cand_id
        if domain and norm_title:
            self.seen_title_domain_pairs[title_pair] = cand_id
        self.seen_content_hashes[content_hash] = cand_id

        return candidate, False
