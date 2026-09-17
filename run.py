#!/usr/bin/env python3
"""
AI Orbit Ingestion Pipeline Runner

Main entrypoint for running the modular ingestion pipeline for the Tools module.
"""

import sys
import argparse
import asyncio
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

from src.utils.logging import setup_logger
from src.discovery.tool_discovery import SeedToolDiscovery, GitHubToolDiscovery
from src.extraction.tool_extractor import ToolExtractor
from src.cleaning.cleaner import ToolCleaner
from src.normalization.normalizer import ToolNormalizer
from src.deduplication.resolver import DeduplicationResolver
from src.qualification.qualifier import GitHubRepoQualifier
from src.verification.website import OfficialWebsiteVerifier
from src.verification.logo import OfficialLogoVerifier
from src.classification.classifier import TaxonomyClassifier
from src.enrichment.orchestrator import LLMOrchestrator
from src.validation.validator import ValidationGate
from src.relationships.mapper import RelationshipMapper
from src.export.exporters import LocalDataExporter
from src.export.google_sheets import GoogleSheetsExporter
from src.storage.repository import StorageRepository
from src.models.tool import ToolRecord, DiscoverySource, EvidenceSource
from src.audit.auditor import DatasetAuditor

logger = setup_logger("pipeline_runner")


def parse_args():
    parser = argparse.ArgumentParser(description="AI Orbit Tools Ingestion Pipeline")
    parser.add_argument("--target", type=int, default=200, help="Target record count for execution milestone")
    parser.add_argument("--source", type=str, default="seed", help="Specific discovery source to run (seed, github, all)")
    parser.add_argument("--enrich-llm", action="store_true", help="Enable LLM description enrichment layer")
    return parser.parse_args()


async def run_pipeline(target_count: int, source_filter: str, enrich_llm: bool = False):
    logger.info(f"Starting pipeline. Target: {target_count}, Source: {source_filter}, Enrich LLM: {enrich_llm}")
    
    # 1. Initialize Modules
    storage = StorageRepository()
    storage.clear_rejected()
    extractor = ToolExtractor()
    cleaner = ToolCleaner()
    normalizer = ToolNormalizer()
    dedup = DeduplicationResolver()
    qualifier = GitHubRepoQualifier()
    web_verifier = OfficialWebsiteVerifier(timeout_seconds=10.0)
    logo_verifier = OfficialLogoVerifier()
    classifier = TaxonomyClassifier()
    llm = LLMOrchestrator()
    validator = ValidationGate()
    rel_mapper = RelationshipMapper()
    local_exporter = LocalDataExporter()
    sheets_exporter = GoogleSheetsExporter()

    # Sources
    sources = []
    if source_filter in ["seed", "all"]:
        sources.append(SeedToolDiscovery())
    if source_filter in ["github", "all"]:
        sources.append(GitHubToolDiscovery())

    accepted_records: List[ToolRecord] = []
    mapping_logs: List[Dict[str, Any]] = []

    # Metrics tracking
    metrics = {
        "discovered": 0,
        "qualified_tool": 0,
        "review_required": 0,
        "rejected_non_tool": 0,
        "duplicates": 0,
        "accepted": 0,
        "rejected_validation": 0,
        "readme_found": 0,
        "readme_missing": 0,
        "rejection_reasons": {},
        "query_counts": {},
        "category_counts": {},
        "desc_source_types": {},
        "pages_fetched": 0,
    }

    rejected_records_log: List[Dict[str, Any]] = []

    # 2. Pipeline Execution Loop
    for source in sources:
        logger.info(f"=== Running Discovery Source: {source.source_name} ===")
        is_github = source.source_name == "GitHub API"
        
        # Pass a sufficiently large limit to discovery so it can paginate to backfill rejections
        discovery_limit = target_count * 10 if is_github else target_count

        async for raw_item in source.discover(limit=discovery_limit):
            try:
                metrics["discovered"] += 1
                
                # Save Raw
                storage.save_raw_record(raw_item, source.source_name)
                
                # Extraction
                extracted = extractor.extract(raw_item, source.source_name)
                
                # Cleaning
                cleaned = cleaner.clean_record(extracted)
                
                # Normalization
                normalized = normalizer.normalize_record(cleaned)
                
                # Qualification (GitHub sources only)
                if is_github:
                    qual_result = qualifier.qualify(normalized)
                    normalized["qualification_status"] = qual_result.status
                    normalized["qualification_reasons"] = qual_result.reasons
                    
                    if qual_result.status == "REJECTED_NON_TOOL":
                        metrics["rejected_non_tool"] += 1
                        reason_str = f"REJECTED_NON_TOOL: {', '.join(qual_result.reasons[:2])}"
                        metrics["rejection_reasons"][reason_str] = metrics["rejection_reasons"].get(reason_str, 0) + 1
                        rej_entry = {
                            "name": normalized.get("name"),
                            "qualification_status": qual_result.status,
                            "reason": f"Qualification: {qual_result.status} — {qual_result.reasons}",
                            "github_repo_url": normalized.get("github_repo_url"),
                            "official_url": normalized.get("official_url"),
                        }
                        rejected_records_log.append(rej_entry)
                        storage.save_rejected(
                            {"tool_name": normalized.get("name"), "url": normalized.get("url"),
                             "github_repo_url": normalized.get("github_repo_url"),
                             "qualification_status": qual_result.status,
                             "qualification_reasons": qual_result.reasons,
                             "signals": qual_result.signals},
                            f"Qualification: {qual_result.status} — {qual_result.reasons}",
                            "QualificationFilter"
                        )
                        continue
                    elif qual_result.status == "REVIEW_REQUIRED":
                        metrics["review_required"] += 1
                        reason_str = f"REVIEW_REQUIRED: {', '.join(qual_result.reasons[:2])}"
                        metrics["rejection_reasons"][reason_str] = metrics["rejection_reasons"].get(reason_str, 0) + 1
                        rej_entry = {
                            "name": normalized.get("name"),
                            "qualification_status": qual_result.status,
                            "reason": f"Qualification: {qual_result.status} — {qual_result.reasons}",
                            "github_repo_url": normalized.get("github_repo_url"),
                            "official_url": normalized.get("official_url"),
                        }
                        rejected_records_log.append(rej_entry)
                        storage.save_rejected(
                            {"tool_name": normalized.get("name"), "url": normalized.get("url"),
                             "github_repo_url": normalized.get("github_repo_url"),
                             "qualification_status": qual_result.status,
                             "qualification_reasons": qual_result.reasons,
                             "signals": qual_result.signals},
                            f"Qualification: {qual_result.status} — {qual_result.reasons}",
                            "QualificationFilter"
                        )
                        continue
                    else:
                        metrics["qualified_tool"] += 1
                
                # README tracking
                if normalized.get("readme_available"):
                    metrics["readme_found"] += 1
                elif is_github:
                    metrics["readme_missing"] += 1

                # Deduplication
                dedup_record, is_duplicate = dedup.resolve(normalized)
                mapping_logs.append(dedup_record)
                
                if is_duplicate:
                    metrics["duplicates"] += 1
                    logger.debug(f"Skipping duplicate record: {dedup_record.get('name')}")
                    continue

                # Determine verification URL: prefer official_url, fall back to github_repo_url
                verify_url = dedup_record.get("official_url") or dedup_record.get("github_repo_url") or dedup_record.get("url")
                verify_record = dict(dedup_record)
                verify_record["url"] = verify_url

                # Website Verification
                verification_result = await web_verifier.verify_website(verify_record)
                
                # If target website is accessible, register as verified external evidence source
                if verification_result.verification_status == "ACCESSIBLE_VERIFIED":
                    verified_site_evidence = {
                        "url": verify_url,
                        "source_type": "OFFICIAL_WEBSITE" if dedup_record.get("official_url") else "GITHUB_REPOSITORY",
                        "trust_level": "OFFICIAL" if dedup_record.get("official_url") else "HIGH",
                        "evidence_type": "WEBSITE_PAGE" if dedup_record.get("official_url") else "CODE_REPOSITORY"
                    }
                    if not any(e.get("url") == verified_site_evidence["url"] for e in dedup_record.get("evidence_sources", [])):
                        dedup_record.setdefault("evidence_sources", []).append(verified_site_evidence)
                    dedup_record["external_evidence_available"] = True
                    dedup_record["external_evidence_url"] = verified_site_evidence["url"]

                # Logo Verification — use verification URL
                logo_record = dict(dedup_record)
                logo_record["url"] = verify_url
                verified = await logo_verifier.discover_logo(logo_record, verification_result)
                # Merge logo fields back
                for k in ["logo_url", "logo_verified", "logo_found", "logo_access_blocked", "logo_source"]:
                    dedup_record[k] = verified.get(k)
                
                # If logo came from GitHub rather than official site, tag it
                if dedup_record.get("logo_source") and not dedup_record.get("official_url"):
                    if dedup_record.get("logo_source") in ("og:image",):
                        dedup_record["logo_source"] = "github_social_preview"

                # Classification (now evidence-based)
                classified = classifier.classify(dedup_record)

                # LLM Enrichment
                enriched = await llm.enrich_description(classified, enrich_llm_flag=enrich_llm)

                # Validation Gate
                is_valid, reject_reason = validator.validate(enriched, verification_result)
                
                if is_valid:
                    metrics["accepted"] += 1
                    
                    # Track categories and description source types for metrics
                    for c in enriched.get("categories", []):
                        metrics["category_counts"][c] = metrics["category_counts"].get(c, 0) + 1
                    stype = enriched.get("description_source_type", "UNKNOWN")
                    metrics["desc_source_types"][stype] = metrics["desc_source_types"].get(stype, 0) + 1

                    # Convert to Pydantic canonical model
                    disc_source = DiscoverySource(
                        name=enriched.get("discovery_source_name") or enriched.get("source_name", "Unknown"),
                        url=enriched.get("discovery_source_url") or enriched.get("source_url", ""),
                        source_type=enriched.get("discovery_source_type") or enriched.get("source_type", "UNKNOWN"),
                        source_trust_level=enriched.get("discovery_source_trust_level") or enriched.get("source_trust_level", "UNKNOWN")
                    )

                    # For ToolRecord: url must be a valid URL. Use official_url or github_repo_url
                    tool_url = enriched.get("official_url") or enriched.get("github_repo_url") or enriched.get("url")
                    tool_official_url = enriched.get("official_url")

                    tool_model = ToolRecord.create_canonical(
                        name=enriched["name"],
                        url=tool_url,
                        official_url=tool_official_url,
                        discovery_source=disc_source,
                        source=disc_source,
                        description=enriched["description"],
                        categories=enriched["categories"],
                        company_name=enriched.get("company_name"),
                        company_url=enriched.get("company_url")
                    )
                    
                    # Evidence sources and external evidence flags
                    tool_model.evidence_sources = [
                        EvidenceSource(**e) if isinstance(e, dict) else e 
                        for e in enriched.get("evidence_sources", [])
                    ]
                    tool_model.external_evidence_available = enriched.get("external_evidence_available", False)
                    tool_model.external_evidence_url = enriched.get("external_evidence_url")

                    # Description grounding & provenance
                    tool_model.description_grounded = enriched.get("description_grounded", False)
                    tool_model.description_source_type = enriched.get("description_source_type")
                    tool_model.description_source_url = enriched.get("description_source_url")
                    tool_model.description_generation_method = enriched.get("description_generation_method")
                    tool_model.llm_provider_used = enriched.get("llm_provider_used", "NONE")
                    tool_model.llm_enrichment_status = enriched.get("llm_enrichment_status", "NOT_CONFIGURED")

                    # Merge verified fields
                    tool_model.logo_url = enriched.get("logo_url")
                    tool_model.logo_verified = enriched.get("logo_verified", False)
                    tool_model.logo_found = enriched.get("logo_found", False)
                    tool_model.logo_access_blocked = enriched.get("logo_access_blocked", False)
                    tool_model.logo_source = enriched.get("logo_source")
                    
                    tool_model.pricing_model = enriched.get("pricing_model")
                    tool_model.verification_status = enriched.get("verification_status", "UNKNOWN")
                    tool_model.verification_reason = enriched.get("verification_reason")
                    tool_model.verification_evidence = enriched.get("verification_evidence", [])
                    tool_model.quality_score = enriched.get("quality_score", 0.0)
                    
                    # GitHub metadata propagation
                    tool_model.github_stars = enriched.get("github_stars")
                    tool_model.github_repo_url = enriched.get("github_repo_url")
                    tool_model.github_repository_verified = bool(tool_model.github_repo_url)
                    
                    # Website verification: True ONLY when an external official website exists and is verified
                    tool_model.website_verified = bool(tool_model.official_url and tool_model.verification_status == "ACCESSIBLE_VERIFIED")
                    
                    accepted_records.append(tool_model)
                    logger.info(f"[ACCEPTED] {tool_model.name} - Score: {tool_model.quality_score} - Status: {tool_model.verification_status} - Categories: {tool_model.categories}")
                    
                    if len(accepted_records) >= target_count:
                        logger.info(f"Target count of {target_count} reached. Stopping discovery.")
                        break
                else:
                    metrics["rejected_validation"] += 1
                    metrics["rejection_reasons"][f"Validation: {reject_reason}"] = metrics["rejection_reasons"].get(f"Validation: {reject_reason}", 0) + 1
                    rej_entry = {
                        "name": enriched.get("name"),
                        "qualification_status": enriched.get("qualification_status", "QUALIFIED_TOOL"),
                        "reason": f"Validation: {reject_reason}",
                        "github_repo_url": enriched.get("github_repo_url"),
                        "official_url": enriched.get("official_url"),
                    }
                    rejected_records_log.append(rej_entry)
                    logger.warning(f"[REJECTED] {enriched.get('name', 'Unknown')}: {reject_reason}")
                    rejection_payload = {
                        "tool_name": enriched.get("name"),
                        "canonical_url": enriched.get("url"),
                        "official_url": enriched.get("official_url"),
                        "github_repo_url": enriched.get("github_repo_url"),
                        "discovery_source": {
                            "name": enriched.get("discovery_source_name") or enriched.get("source_name"),
                            "url": enriched.get("discovery_source_url") or enriched.get("source_url"),
                            "type": enriched.get("discovery_source_type") or enriched.get("source_type"),
                            "trust_level": enriched.get("discovery_source_trust_level") or enriched.get("source_trust_level")
                        },
                        "evidence_sources": enriched.get("evidence_sources", []),
                        "external_evidence_available": enriched.get("external_evidence_available", False),
                        "external_evidence_url": enriched.get("external_evidence_url"),
                        "verification_status": verification_result.verification_status,
                        "http_status": verification_result.http_status,
                        "description": enriched.get("description"),
                        "description_grounded": enriched.get("description_grounded"),
                        "description_generation_method": enriched.get("description_generation_method"),
                        "evidence": [e.model_dump(mode="json") for e in verification_result.evidence],
                        "raw_item": raw_item
                    }
                    storage.save_rejected(rejection_payload, reject_reason, "ValidationGate")
                    
            except Exception as e:
                logger.error(f"Error processing record {raw_item.get('name')}: {e}")
                storage.save_rejected(raw_item, str(e), "PipelineException")

        # Capture discovery stats
        if hasattr(source, "pages_fetched"):
            metrics["pages_fetched"] += source.pages_fetched
        if hasattr(source, "query_counts"):
            for qk, qv in source.query_counts.items():
                metrics["query_counts"][qk] = metrics["query_counts"].get(qk, 0) + qv

        if len(accepted_records) >= target_count:
            break

    # 3. Post-Processing & Export
    logger.info(f"=== Pipeline Completed. Accepted Records: {len(accepted_records)} ===")
    logger.info(f"=== Metrics: {metrics} ===")
    
    audit_results = []
    if accepted_records:
        storage.save_validated(accepted_records)
        rel_mapper.generate_relationships(accepted_records)
        local_exporter.export_all(accepted_records, mapping_logs)
        sheets_exporter.export(accepted_records)
        
        # Phase 3B Dataset Audit
        auditor = DatasetAuditor()
        audit_results = auditor.audit_all(accepted_records)

    # 4. Generate Quality Report
    generate_quality_report(accepted_records, rejected_records_log, metrics, audit_results, target_count, llm.metrics)


def generate_quality_report(
    accepted_records: List[ToolRecord],
    rejected_records: List[Dict[str, Any]],
    metrics: Dict[str, Any],
    audit_results: List[Dict[str, Any]],
    target_count: int,
    llm_metrics: Optional[Dict[str, Any]] = None
):
    """Generates quality_report.md containing Phase 3B audit and Phase 4 LLM Orchestration metrics."""
    stars = [r.github_stars for r in accepted_records if r.github_stars is not None]
    stars_with_val = len(stars)
    min_stars = min(stars) if stars else 0
    max_stars = max(stars) if stars else 0
    import statistics
    median_stars = int(statistics.median(stars)) if stars else 0

    official_urls_count = sum(1 for r in accepted_records if r.official_url)
    github_repos_count = sum(1 for r in accepted_records if r.github_repo_url)

    # Verification and semantic counts
    website_verified_count = sum(1 for r in accepted_records if r.website_verified)
    github_repo_verified_count = sum(1 for r in accepted_records if r.github_repository_verified)
    logo_verified_count = sum(1 for r in accepted_records if r.logo_verified)
    logo_social_preview_count = sum(1 for r in accepted_records if r.logo_source == "github_social_preview")

    # Grounded description count
    grounded_desc_count = sum(1 for r in accepted_records if r.description_grounded)

    # Audit summary counts
    audit_pass = sum(1 for a in audit_results if a.get("overall_audit_status") == "PASS")
    audit_corrected = sum(1 for a in audit_results if a.get("overall_audit_status") == "CORRECTED")
    audit_review = sum(1 for a in audit_results if a.get("overall_audit_status") == "REVIEW_REQUIRED")
    audit_reject = sum(1 for a in audit_results if a.get("overall_audit_status") == "REJECT")

    report_lines = [
        "# Quality Report — Phase 3B & Phase 4",
        "",
        "## Status & Summary",
        f"- **Execution Target**: {target_count}",
        f"- **Final Accepted Qualified Records**: {len(accepted_records)}",
        f"- **Target Reached**: {'YES' if len(accepted_records) >= target_count else 'NO'}",
        f"- **Audit Output Log**: `data/audits/phase_3b_audit.jsonl`",
        f"- **Date**: 2026-09-17",
        "",
        "## Deterministic Audit Breakdown",
        f"- **Total Records Audited**: {len(audit_results)}",
        f"- **PASS (Zero Semantic Issues)**: {audit_pass}",
        f"- **CORRECTED (Semantics Corrected)**: {audit_corrected}",
        f"- **REVIEW_REQUIRED**: {audit_review}",
        f"- **REJECT**: {audit_reject}",
        "",
        "## Verification & Semantic Precision Metrics",
        f"- **Official External Website URLs**: {official_urls_count}",
        f"- **Website Verified (`website_verified = True`)**: {website_verified_count} (True ONLY for verified external homepages)",
        f"- **GitHub Repository Verified (`github_repository_verified = True`)**: {github_repo_verified_count}",
        f"- **Verified Brand Logos (`logo_verified = True`)**: {logo_verified_count}",
        f"- **GitHub Social Preview Fallbacks (`logo_source = 'github_social_preview'`)**: {logo_social_preview_count} (`logo_verified = False`)",
        "",
        "## Discovery & Qualification Metrics",
        f"- **Total Candidates Discovered**: {metrics.get('discovered', 0)}",
        f"- **Pages Fetched**: {metrics.get('pages_fetched', 0)}",
        f"- **QUALIFIED_TOOL**: {metrics.get('qualified_tool', 0)}",
        f"- **REVIEW_REQUIRED**: {metrics.get('review_required', 0)}",
        f"- **REJECTED_NON_TOOL**: {metrics.get('rejected_non_tool', 0)}",
        "",
        "## README & Description Grounding Metrics",
        f"- **README Found**: {metrics.get('readme_found', 0)}",
        f"- **README Missing**: {metrics.get('readme_missing', 0)}",
        f"- **Grounded Descriptions**: {grounded_desc_count} / {len(accepted_records)}",
        f"- **Description Source Types**:",
    ]

    for sk, sv in metrics.get("desc_source_types", {}).items():
        report_lines.append(f"  - `{sk}`: {sv}")

    report_lines.extend([
        "",
        "## Category Distribution (Accepted Dataset)",
    ])

    for ck, cv in metrics.get("category_counts", {}).items():
        report_lines.append(f"- **{ck}**: {cv}")

    report_lines.extend([
        "",
        "## GitHub Star Metrics",
        f"- **Records with github_stars**: {stars_with_val}",
        f"- **Minimum Stars**: {min_stars}",
        f"- **Maximum Stars**: {max_stars}",
        f"- **Median Stars**: {median_stars}",
        "",
        "## Deduplication & Validation Metrics",
        f"- **Duplicates Merged**: {metrics.get('duplicates', 0)}",
        f"- **Accepted**: {metrics.get('accepted', 0)}",
        f"- **Rejected Validation**: {metrics.get('rejected_validation', 0)}",
        "",
        "## Top Qualification & Validation Rejection Reasons",
    ])

    top_rejections = sorted(metrics.get("rejection_reasons", {}).items(), key=lambda x: x[1], reverse=True)[:10]
    for r_reason, r_count in top_rejections:
        report_lines.append(f"- `{r_reason}`: {r_count}")

    # Add Phase 4 section if LLM metrics are present
    if llm_metrics:
        p_att = llm_metrics.get("provider_attempts", {})
        p_suc = llm_metrics.get("provider_successes", {})
        p_fail = llm_metrics.get("provider_failures", {})

        report_lines.extend([
            "",
            "# Phase 4 — LLM Orchestration",
            "",
            "## Provider Fallback Architecture & Configuration",
            "- **Primary Provider**: Gemini Flash (`GEMINI_API_KEY`)",
            "- **Fallback 1**: Groq Llama-3 (`GROQ_API_KEY`)",
            "- **Fallback 2**: DeepSeek (`DEEPSEEK_API_KEY`)",
            "- **Test & Safe Mode**: Deterministic source-derived fallback when API credentials are absent (`llm_enrichment_status = NOT_CONFIGURED`).",
            "",
            "## LLM Generation & Orchestration Metrics",
            f"- **Total Records Sent to LLM**: {llm_metrics.get('llm_records_processed', 0)}",
            f"- **Gemini Attempts / Successes / Failures**: {p_att.get('Gemini', 0)} / {p_suc.get('Gemini', 0)} / {p_fail.get('Gemini', 0)}",
            f"- **Groq Attempts / Successes / Failures**: {p_att.get('Groq', 0)} / {p_suc.get('Groq', 0)} / {p_fail.get('Groq', 0)}",
            f"- **DeepSeek Attempts / Successes / Failures**: {p_att.get('DeepSeek', 0)} / {p_suc.get('DeepSeek', 0)} / {p_fail.get('DeepSeek', 0)}",
            f"- **Total Fallback Events**: {llm_metrics.get('fallback_events', 0)}",
            f"- **Malformed Responses**: {llm_metrics.get('malformed_responses', 0)}",
            f"- **Grounded LLM Descriptions**: {llm_metrics.get('grounded_descriptions', 0)}",
            f"- **Ungrounded LLM Responses**: {llm_metrics.get('ungrounded_responses', 0)}",
            f"- **Records with No Usable Description**: {llm_metrics.get('records_no_usable_description', 0)}",
            "",
            "## Processed Records LLM Detail",
            "",
        ])

        for i, rec in enumerate(accepted_records, 1):
            report_lines.extend([
                f"### {i}. {rec.name}",
                f"- **Description**: {rec.description}",
                f"- **LLM Provider Used**: {rec.llm_provider_used or 'NONE'}",
                f"- **Description Source Type**: {rec.description_source_type}",
                f"- **Description Source URL**: {rec.description_source_url}",
                f"- **Description Grounded**: {rec.description_grounded}",
                f"- **LLM Enrichment Status**: {rec.llm_enrichment_status}",
                f"- **Description Generation Method**: {rec.description_generation_method}",
                "",
            ])

    report_lines.extend([
        "## Semantic Audit Audit Trail & Verification Directives",
        "- **Curriculum & Non-Tool Filtering**: Repositories matching academy, course, tutorial, papers, or benchmark patterns are strictly excluded from accepted records.",
        "- **Website vs Repository Verification**: `website_verified` is strictly `False` unless a standalone external official domain is present and accessible.",
        "- **Logo Verification Semantics**: GitHub `og:image` social previews are retained for preview display but marked `logo_verified = False`.",
        "- **Grounding Hierarchy**: Slogan-only descriptions ('runs anywhere', etc.) are replaced with substantive initial paragraphs extracted from official README documentation.",
    ])

    with open("quality_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    logger.info("Generated quality_report.md successfully.")


def main():
    args = parse_args()
    asyncio.run(run_pipeline(args.target, args.source, args.enrich_llm))


if __name__ == "__main__":
    main()

