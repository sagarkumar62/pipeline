"""
Phase 3B Dataset Auditor

Performs deterministic audit of canonical Tool records, producing data/audits/phase_3b_audit.jsonl
with structured decisions for qualification, categories, official_url, logo, description, and overall status.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from src.models.tool import ToolRecord
from src.utils.logging import setup_logger

logger = setup_logger("dataset_auditor")


class DatasetAuditor:
    """
    Audits canonical Tool records against Phase 3B quality & semantic rules.
    Outputs records to data/audits/phase_3b_audit.jsonl.
    """

    def __init__(self, audit_dir: str = "data/audits"):
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.audit_filepath = self.audit_dir / "phase_3b_audit.jsonl"

    def audit_record(self, record: ToolRecord) -> Dict[str, Any]:
        """
        Audits a single canonical ToolRecord.
        Returns detailed audit dict.
        """
        issues: List[str] = []
        qual_reasons: List[str] = []
        cat_reasons: List[str] = []
        
        qual_decision = "PASS"
        cat_decision = "PASS"
        url_decision = "PASS"
        logo_decision = "PASS"
        desc_decision = "PASS"

        # 1. Qualification Audit
        name_lower = record.name.lower()
        desc_lower = (record.description or "").lower()

        # Hard negative terms for qualification
        non_tool_terms = ["curriculum", "course", "academy", "tutorial", "awesome list", "paper collection", "dataset", "benchmark", "daily arxiv"]
        matched_terms = [t for t in non_tool_terms if t in name_lower or t in desc_lower]

        if matched_terms:
            qual_decision = "REJECT"
            qual_reasons.append(f"Non-tool keywords detected in record: {matched_terms}")
            issues.append(f"Qualification Failure: {matched_terms}")
        elif record.website_verified is False and not record.github_repo_url:
            qual_decision = "REVIEW_REQUIRED"
            qual_reasons.append("Missing both verified official website and GitHub repository evidence")
            issues.append("Unverified Identity")

        # 2. Category Audit
        categories = record.categories
        if not categories:
            cat_decision = "REVIEW_REQUIRED"
            cat_reasons.append("Uncategorized record")
            issues.append("Missing Taxonomy Category")
        
        # Check specific misclassification cases
        if "judge0" in name_lower or "code execution" in desc_lower:
            if "Agents" in categories:
                cat_decision = "CORRECTED"
                cat_reasons.append("Removed misclassified 'Agents' category from code execution API")
                issues.append("Category Correction: Code execution API is not an Agent")

        if "prompt-optimizer" in name_lower or "prompt optimizer" in desc_lower:
            if "Models" in categories:
                cat_decision = "CORRECTED"
                cat_reasons.append("Removed misclassified 'Models' category from prompt utility")
                issues.append("Category Correction: Prompt utility is not a Model")

        # 3. Official URL Audit
        if not record.official_url or "github.com" in record.official_url.lower():
            if record.website_verified:
                url_decision = "CORRECTED"
                issues.append("Website Verification Correction: website_verified must be False when official_url is null or GitHub-only")

        # 4. Logo Audit
        if record.logo_source == "github_social_preview" and record.logo_verified:
            logo_decision = "CORRECTED"
            issues.append("Logo Verification Correction: logo_verified must be False for github_social_preview fallback assets")

        # 5. Description Audit
        if record.description and (len(record.description) < 20 or record.description.lower().startswith("runs anywhere")):
            desc_decision = "CORRECTED"
            issues.append("Description Grounding Correction: slogan or low-quality description present")

        # Overall Status
        if qual_decision == "REJECT":
            overall_status = "REJECT"
        elif "REVIEW_REQUIRED" in [qual_decision, cat_decision, url_decision, logo_decision, desc_decision]:
            overall_status = "REVIEW_REQUIRED"
        elif "CORRECTED" in [cat_decision, url_decision, logo_decision, desc_decision]:
            overall_status = "CORRECTED"
        else:
            overall_status = "PASS"

        audit_entry = {
            "record_id": record.id,
            "tool_name": record.name,
            "qualification_decision": qual_decision,
            "qualification_reasons": qual_reasons if qual_reasons else ["Legitimate usable software tool"],
            "category_decision": cat_decision,
            "category_reasons": cat_reasons if cat_reasons else [f"Categories supported: {record.categories}"],
            "official_url_decision": url_decision,
            "logo_decision": logo_decision,
            "description_decision": desc_decision,
            "overall_audit_status": overall_status,
            "issues": issues,
        }
        return audit_entry

    def audit_all(self, records: List[ToolRecord]) -> List[Dict[str, Any]]:
        """Audits all Tool records and saves to JSONL."""
        audits = []
        with open(self.audit_filepath, "w", encoding="utf-8") as f:
            for r in records:
                entry = self.audit_record(r)
                audits.append(entry)
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        logger.info(f"Audited {len(records)} records. Results saved to {self.audit_filepath}")
        return audits
