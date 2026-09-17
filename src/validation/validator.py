from typing import Dict, Any, Tuple, Optional
from src.utils.logging import setup_logger
from src.models.tool import VerificationResult

logger = setup_logger("validation_gate")


class ValidationGate:
    """
    Validation gate enforcing strict requirements for final ToolRecord acceptance.
    Calculates independent quality score metrics.
    """

    def calculate_quality_score(self, record: Dict[str, Any], verification_result: VerificationResult) -> float:
        """
        Calculates independent quality score metrics:
        - qualification_confidence (0.2 max)
        - website_verification (0.3 max for verified external website; 0.15 for verified GitHub repo)
        - source_quality (0.1 max)
        - description_quality (0.2 max)
        - category_correctness (0.1 max)
        - logo_verification (0.1 max)
        """
        score = 0.0

        # Qualification Confidence (0.2 max)
        if record.get("qualification_status") == "QUALIFIED_TOOL":
            score += 0.2

        # Website Verification / Official URL (0.3 max)
        has_official_site = bool(record.get("official_url"))
        if has_official_site and verification_result.verification_status == "ACCESSIBLE_VERIFIED":
            score += 0.3
        elif verification_result.verification_status == "ACCESSIBLE_VERIFIED" or record.get("github_repository_verified"):
            score += 0.15  # GitHub repo verified, but no verified external official site

        # Source Quality (0.1 max)
        trust_level = record.get("source_trust_level", "UNKNOWN")
        if trust_level in ["OFFICIAL", "HIGH"]:
            score += 0.1
        elif trust_level == "MEDIUM":
            score += 0.05

        # Description Quality (0.2 max)
        desc = record.get("description", "")
        if desc and len(desc) >= 20 and record.get("description_grounded", False):
            # Penalize slogan-only short descriptions
            if len(desc) >= 30 and not desc.lower().startswith("runs anywhere"):
                score += 0.2
            else:
                score += 0.1

        # Category Correctness (0.1 max)
        if record.get("categories") and len(record["categories"]) > 0:
            score += 0.1

        # Logo Verification (0.1 max — ONLY when logo_verified is True)
        if record.get("logo_verified", False):
            score += 0.1

        return round(score, 2)

    def validate(self, record: Dict[str, Any], verification_result: VerificationResult) -> Tuple[bool, Optional[str]]:
        """
        Evaluates evidence-based acceptance rules according to Real Source Discovery & Provenance Audit.
        """
        # 0. Qualification check (if present)
        qual_status = record.get("qualification_status")
        if qual_status:
            if qual_status == "REJECTED_NON_TOOL":
                return False, f"Qualification: REJECTED_NON_TOOL — {record.get('qualification_reasons', [])}"
            elif qual_status == "REVIEW_REQUIRED":
                return False, f"Qualification: REVIEW_REQUIRED — {record.get('qualification_reasons', [])}"

        # 1. Valid Name
        name = record.get("name")
        if not name or len(name.strip()) < 2:
            return False, "Invalid or missing tool name"

        # 2. Valid Canonical / Official URL or GitHub repo URL
        url = record.get("official_url") or record.get("github_repo_url") or record.get("url")
        if not url or not url.startswith(("http://", "https://")):
            return False, "Invalid or missing canonical URL"

        # 3. Discovery Provenance
        disc_name = record.get("discovery_source_name") or record.get("source_name")
        disc_url = record.get("discovery_source_url") or record.get("source_url")
        disc_type = record.get("discovery_source_type") or record.get("source_type", "UNKNOWN")
        source_trust = record.get("discovery_source_trust_level") or record.get("source_trust_level", "UNKNOWN")

        if not disc_name or not disc_url:
            return False, "Missing discovery provenance metadata"

        # Check for malformed external URL where external URL is claimed
        if disc_type in ["API", "OFFICIAL_REGISTRY"] and not disc_url.startswith(("http://", "https://")):
            return False, f"Malformed external discovery URL: {disc_url}"

        # 4. Description Present, Grounded, and References Evidence Source
        desc = record.get("description")
        if not desc or len(desc.strip()) < 10:
            return False, "Description missing or too short"
        if not record.get("description_grounded", False):
            return False, "Description is not grounded in verifiable source or website evidence"
        desc_source = record.get("description_source_url") or record.get("external_evidence_url") or record.get("github_repo_url") or record.get("discovery_source_url") or record.get("source_url")
        if not desc_source:
            return False, "No evidence source URL for factual description"

        # 5. Evidence-based Identity Verification
        # Note: Do NOT reject merely for HTTP 403, HTTP 429, or missing logo when sufficient independent identity evidence exists
        identity_established = False
        if verification_result.verification_status == "ACCESSIBLE_VERIFIED":
            identity_established = True
            
        elif verification_result.verification_status in ["ACCESS_BLOCKED", "RATE_LIMITED"] or verification_result.http_status in [403, 429]:
            # Can be accepted if there is authoritative independent evidence (HIGH or OFFICIAL trust)
            has_authoritative_evidence = source_trust in ["OFFICIAL", "HIGH"]
            # Also check evidence sources list
            if any(e.get("trust_level") in ["OFFICIAL", "HIGH"] for e in record.get("evidence_sources", [])):
                has_authoritative_evidence = True

            if has_authoritative_evidence and verification_result.official_domain_match:
                identity_established = True
                logger.info(f"Accepted {name} via independent authoritative evidence despite HTTP {verification_result.http_status}.")
            else:
                return False, f"Identity Verification Failed: ACCESS_BLOCKED (HTTP {verification_result.http_status}) with insufficient source trust level ('{source_trust}') to confirm identity"

        if not identity_established:
            reason = verification_result.reason or "Identity could not be established"
            return False, f"Identity Verification Failed: {reason}"

        # 6. Valid Categories
        categories = record.get("categories")
        if not categories or len(categories) == 0:
            return False, "No taxonomy categories assigned"

        # Calculate & attach final quality score (logo failure reduces score but does NOT reject)
        record["quality_score"] = self.calculate_quality_score(record, verification_result)
        
        # Merge verification status strings for output
        record["verification_status"] = verification_result.verification_status
        record["verification_reason"] = verification_result.reason
        
        # Keep evidence as objects for ToolRecord parsing
        record["verification_evidence"] = verification_result.evidence
        
        return True, None
