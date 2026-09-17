from typing import Dict, List, Optional, Tuple, Any
from rapidfuzz import fuzz
from src.utils.logging import setup_logger

logger = setup_logger("deduplication")


class DeduplicationResolver:
    """
    Deterministic entity resolution engine for Tool records.
    Combines canonical domain identity, URL matching, GitHub repo identity,
    canonical name blocking, and RapidFuzz fuzzy candidate comparison.
    """

    def __init__(self, fuzzy_threshold: float = 88.0):
        self.fuzzy_threshold = fuzzy_threshold
        self._seen_ids: Dict[str, Dict[str, Any]] = {}
        self._domain_map: Dict[str, str] = {}  # domain -> canonical_id
        self._github_repo_map: Dict[str, str] = {}  # github_repo_url -> canonical_id
        self._name_map: Dict[str, str] = {}  # canonical_name -> canonical_id
        self._blocked_candidates: Dict[str, List[str]] = {}  # block_key -> list of canonical_ids

    def load_baseline(self, records: List[Dict[str, Any]]) -> int:
        """
        Pre-loads existing golden baseline records as immutable deduplication anchors.
        A newly discovered candidate matching any baseline entity will be classified
        as a duplicate rather than creating a secondary record.
        """
        loaded_count = 0
        for r in records:
            if isinstance(r, dict):
                rec = dict(r)
            elif hasattr(r, "model_dump"):
                rec = r.model_dump()
            else:
                continue

            rec_id = rec.get("id")
            if not rec_id:
                continue

            rec["is_baseline"] = True
            self._seen_ids[rec_id] = rec

            # Domain indexing
            official_url = rec.get("official_url") or ""
            url = rec.get("url") or ""
            domain = rec.get("domain")
            if not domain:
                from src.utils.urls import extract_domain
                domain = extract_domain(official_url or url)
            if domain:
                self._domain_map[domain] = rec_id

            # GitHub repo indexing
            github_url = rec.get("github_repo_url")
            if github_url:
                from src.utils.urls import normalize_url
                norm_gh = normalize_url(github_url)
                if norm_gh:
                    self._github_repo_map[norm_gh] = rec_id

            # Name indexing & blocking
            name = rec.get("name") or ""
            canonical_name = rec.get("canonical_name") or name.lower().strip()
            if canonical_name:
                self._name_map[canonical_name] = rec_id
                block_key = canonical_name[:3] if len(canonical_name) >= 3 else canonical_name
                self._blocked_candidates.setdefault(block_key, []).append(rec_id)

            loaded_count += 1

        logger.info(f"Successfully loaded {loaded_count} baseline records as deduplication anchors.")
        return loaded_count

    def resolve(self, record: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Resolves a normalized tool record against existing entities using deterministic hierarchy:
        1. Exact stable record ID
        2. Normalized GitHub repo identity
        3. Normalized official domain identity
        4. Canonical normalized name blocking
        5. Fuzzy comparison only within the blocked candidate set
        """
        rec_id = record["id"]
        domain = record.get("domain")
        canonical_name = record.get("canonical_name", "")
        github_repo_url = record.get("github_repo_url")

        # 1. Exact Stable ID match
        if rec_id in self._seen_ids:
            canonical_rec = self._seen_ids[rec_id]
            record["duplicate_of"] = canonical_rec["id"]
            record["match_method"] = "exact_stable_id"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical_rec.get("is_baseline", False)
            logger.info(f"Duplicate found by exact stable ID: '{record['name']}' -> '{canonical_rec['name']}'")
            return record, True

        # 2. GitHub Repo URL identity match
        if github_repo_url:
            from src.utils.urls import normalize_url
            norm_gh = normalize_url(github_repo_url)
            if norm_gh and norm_gh in self._github_repo_map:
                canonical_id = self._github_repo_map[norm_gh]
                canonical_rec = self._seen_ids[canonical_id]
                record["duplicate_of"] = canonical_id
                record["match_method"] = "github_repo_url_match"
                record["match_confidence"] = 1.0
                record["is_baseline_match"] = canonical_rec.get("is_baseline", False)
                logger.info(f"Duplicate found by GitHub repo URL: '{record['name']}' -> '{canonical_rec['name']}'")
                return record, True

        # 3. Canonical Domain match
        if domain and domain in self._domain_map:
            canonical_id = self._domain_map[domain]
            canonical_rec = self._seen_ids[canonical_id]
            ex_canon_name = canonical_rec.get("canonical_name", "")
            sim = fuzz.token_sort_ratio(canonical_name, ex_canon_name)
            if sim >= 70.0 or canonical_name in ex_canon_name or ex_canon_name in canonical_name:
                record["duplicate_of"] = canonical_id
                record["match_method"] = "domain_identity_match"
                record["match_confidence"] = round(sim / 100.0, 2)
                record["is_baseline_match"] = canonical_rec.get("is_baseline", False)
                logger.info(f"Duplicate found by domain '{domain}': '{record['name']}' -> '{canonical_rec['name']}'")
                return record, True


        # 4. Canonical Name Exact Blocking Match
        if canonical_name and canonical_name in self._name_map:
            canonical_id = self._name_map[canonical_name]
            canonical_rec = self._seen_ids[canonical_id]
            record["duplicate_of"] = canonical_id
            record["match_method"] = "canonical_name_exact_match"
            record["match_confidence"] = 1.0
            record["is_baseline_match"] = canonical_rec.get("is_baseline", False)
            logger.info(f"Duplicate found by canonical name exact match: '{record['name']}' -> '{canonical_rec['name']}'")
            return record, True

        # 5. Fuzzy Name Similarity ONLY within candidate block (block_key = first 3 chars of name)
        block_key = canonical_name[:3] if len(canonical_name) >= 3 else canonical_name
        candidate_ids = self._blocked_candidates.get(block_key, [])

        for candidate_id in candidate_ids:
            if candidate_id not in self._seen_ids:
                continue
            existing_rec = self._seen_ids[candidate_id]
            ex_name = existing_rec.get("canonical_name", "")
            score = fuzz.token_sort_ratio(canonical_name, ex_name)

            if score >= self.fuzzy_threshold:
                same_company = False
                if record.get("company_name") and existing_rec.get("company_name"):
                    comp_sim = fuzz.ratio(
                        record["company_name"].lower(),
                        existing_rec["company_name"].lower()
                    )
                    same_company = comp_sim >= 85

                if same_company or score >= 95.0:
                    record["duplicate_of"] = candidate_id
                    record["match_method"] = "rapidfuzz_blocked_candidate"
                    record["match_confidence"] = round(score / 100.0, 2)
                    record["is_baseline_match"] = existing_rec.get("is_baseline", False)
                    logger.info(f"Duplicate found by RapidFuzz blocked match ({score}%): '{record['name']}' -> '{existing_rec['name']}'")
                    return record, True

        # Register as a new canonical entity
        self._seen_ids[rec_id] = record
        if domain:
            self._domain_map[domain] = rec_id
        if github_repo_url:
            from src.utils.urls import normalize_url
            norm_gh = normalize_url(github_repo_url)
            if norm_gh:
                self._github_repo_map[norm_gh] = rec_id
        if canonical_name:
            self._name_map[canonical_name] = rec_id
            self._blocked_candidates.setdefault(block_key, []).append(rec_id)

        record["duplicate_of"] = None
        record["match_method"] = None
        record["match_confidence"] = None
        record["is_baseline_match"] = False
        return record, False
