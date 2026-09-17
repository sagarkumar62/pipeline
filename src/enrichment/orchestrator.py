"""
Phase 4 LLM Orchestrator

Orchestrates description enrichment with evidence packaging, multi-provider fallback,
grounding validation, deterministic fallback, and comprehensive metrics tracking.
"""

import re
from typing import Dict, Any, List, Optional
from src.enrichment.schema import EvidencePackage, LLMResult, StructuredLLMOutput
from src.enrichment.llm_base import BaseLLMProvider
from src.enrichment.gemini import GeminiProvider
from src.enrichment.groq import GroqProvider
from src.enrichment.deepseek import DeepSeekProvider
from src.enrichment.validator import GroundingValidator
from src.enrichment.quality import DescriptionQualityChecker
from src.utils.logging import setup_logger

logger = setup_logger("llm_orchestrator")


class LLMOrchestrator:
    """
    Orchestrates evidence packaging, multi-provider fallback execution (Gemini -> Groq -> DeepSeek),
    grounding validation, quality checking, controlled regeneration, and deterministic source fallback.
    """

    def __init__(self, providers: Optional[List[BaseLLMProvider]] = None):
        self.providers = providers or [
            GeminiProvider(),
            GroqProvider(),
            DeepSeekProvider()
        ]
        self.validator = GroundingValidator()
        self.quality_checker = DescriptionQualityChecker()
        self.metrics = {
            "llm_records_processed": 0,
            "provider_attempts": {"Gemini": 0, "Groq": 0, "DeepSeek": 0},
            "provider_successes": {"Gemini": 0, "Groq": 0, "DeepSeek": 0},
            "provider_failures": {"Gemini": 0, "Groq": 0, "DeepSeek": 0},
            "fallback_events": 0,
            "malformed_responses": 0,
            "grounded_descriptions": 0,
            "ungrounded_responses": 0,
            "records_no_usable_description": 0,
            "quality_failures": 0,
            "generic_descriptions": 0,
            "low_information_grounded": 0,
            "regeneration_attempts": 0,
            "record_provider_log": []
        }

    def construct_evidence_package(self, record: Dict[str, Any], max_chars: int = 3500) -> EvidencePackage:
        """
        Constructs a structured EvidencePackage containing ONLY information already collected by the pipeline.
        Order of priority:
        1. Verified official website metadata/content
        2. GitHub repository description
        3. GitHub README excerpt
        4. GitHub topics
        5. Other legitimate metadata
        """
        tool_name = record.get("name", "")
        official_url = record.get("official_url")
        website_content = record.get("meta_description") or record.get("page_title")
        repo_desc = record.get("description") or record.get("raw_description")
        github_repo_url = record.get("github_repo_url")
        readme_content = record.get("readme_content")
        readme_url = record.get("readme_url") or (f"{github_repo_url}/blob/main/README.md" if github_repo_url else None)
        topics = record.get("topics") or []
        company = record.get("company_name")

        # Collect legitimate source URLs present in record
        source_urls = []
        for url_key in ["official_url", "github_repo_url", "readme_url", "external_evidence_url", "url", "source_url"]:
            val = record.get(url_key)
            if val and isinstance(val, str) and val.startswith("http") and val not in source_urls:
                source_urls.append(val)

        # Process README excerpt and apply input character limit
        readme_excerpt = None
        truncated = False
        if readme_content:
            clean_readme = self._clean_readme(readme_content)
            # Budget check
            current_len = len(tool_name) + len(website_content or "") + len(repo_desc or "") + len(" ".join(topics))
            avail_chars = max(500, max_chars - current_len)

            if len(clean_readme) > avail_chars:
                readme_excerpt = clean_readme[:avail_chars] + "...[TRUNCATED]"
                truncated = True
            else:
                readme_excerpt = clean_readme

        return EvidencePackage(
            tool_name=tool_name,
            official_website_content=website_content,
            official_website_url=official_url if record.get("website_verified") else None,
            repository_description=repo_desc,
            github_repo_url=github_repo_url,
            readme_excerpt=readme_excerpt,
            readme_url=readme_url,
            topics=topics,
            company_name=company,
            source_urls=source_urls,
            truncated=truncated
        )

    async def enrich_description(self, record: Dict[str, Any], enrich_llm_flag: bool = False) -> Dict[str, Any]:
        """
        Enriches record description.
        If enrich_llm_flag is True and providers are available, executes provider fallback chain.
        Otherwise, performs deterministic source-derived fallback.
        """
        tool_name = record.get("name", "")
        available_providers = [p for p in self.providers if p.is_available]

        # Case 1: LLM enrichment requested and providers available
        if enrich_llm_flag and available_providers:
            self.metrics["llm_records_processed"] += 1
            evidence_pkg = self.construct_evidence_package(record)

            for provider in available_providers:
                p_name = provider.provider_name
                self.metrics["provider_attempts"][p_name] = self.metrics["provider_attempts"].get(p_name, 0) + 1

                try:
                    res: LLMResult = await provider.generate_description(evidence_pkg)

                    if res.status == "SUCCESS" and res.description:
                        # Construct StructuredLLMOutput for validation
                        structured_output = StructuredLLMOutput(
                            description=res.description,
                            grounded=res.grounded,
                            confidence=res.confidence,
                            evidence_used=[
                                {"source_url": e.get("source_url", ""), "source_type": e.get("source_type", "UNKNOWN")}
                                for e in res.evidence_used
                            ]
                        )

                        is_grounded, val_reason = self.validator.validate(structured_output, evidence_pkg)

                        if is_grounded:
                            cleaned_desc = re.sub(r'^["\']|["\']$', '', res.description.strip())
                            quality_flag, is_quality_pass = self.quality_checker.check_quality(cleaned_desc, tool_name)

                            # Controlled regeneration if low-information or generic
                            if not is_quality_pass and quality_flag in ["LOW_INFORMATION", "GENERIC"]:
                                logger.info(f"Description for '{tool_name}' flagged as {quality_flag}. Attempting 1-attempt regeneration...")
                                self.metrics["regeneration_attempts"] += 1
                                
                                # Instruct provider for higher specificity
                                regen_pkg = evidence_pkg.model_copy()
                                regen_pkg.repository_description = (
                                    f"IMPORTANT INSTRUCTION: Make the description specific to what '{tool_name}' actually does. "
                                    f"Avoid generic marketing slogans.\nExisting repository info: {evidence_pkg.repository_description or ''}"
                                )
                                try:
                                    regen_res = await provider.generate_description(regen_pkg)
                                    if regen_res.status == "SUCCESS" and regen_res.description:
                                        regen_structured = StructuredLLMOutput(
                                            description=regen_res.description,
                                            grounded=regen_res.grounded,
                                            confidence=regen_res.confidence,
                                            evidence_used=[
                                                {"source_url": e.get("source_url", ""), "source_type": e.get("source_type", "UNKNOWN")}
                                                for e in regen_res.evidence_used
                                            ]
                                        )
                                        regen_is_grounded, _ = self.validator.validate(regen_structured, evidence_pkg)
                                        if regen_is_grounded:
                                            regen_desc = re.sub(r'^["\']|["\']$', '', regen_res.description.strip())
                                            regen_q_flag, regen_q_pass = self.quality_checker.check_quality(regen_desc, tool_name)
                                            if regen_q_pass:
                                                cleaned_desc = regen_desc
                                                quality_flag = "VALID"
                                            elif quality_flag == "LOW_INFORMATION":
                                                quality_flag = "LOW_INFORMATION_GROUNDED"
                                                self.metrics["low_information_grounded"] += 1
                                except Exception as r_err:
                                    logger.warning(f"Regeneration attempt failed for '{tool_name}': {r_err}")
                                    if quality_flag == "LOW_INFORMATION":
                                        quality_flag = "LOW_INFORMATION_GROUNDED"
                                        self.metrics["low_information_grounded"] += 1
                            elif not is_quality_pass:
                                self.metrics["quality_failures"] += 1
                                if quality_flag == "GENERIC":
                                    self.metrics["generic_descriptions"] += 1

                            record["description"] = cleaned_desc
                            record["description_grounded"] = True
                            record["description_source_type"] = self._determine_source_type(res, evidence_pkg)
                            record["description_source_url"] = res.evidence_used[0].get("source_url") if res.evidence_used else (record.get("official_url") or record.get("github_repo_url"))
                            record["description_generation_method"] = f"LLM_{p_name.upper()}"
                            record["llm_provider_used"] = p_name
                            record["llm_enrichment_status"] = "SUCCESS"
                            record["quality_flag"] = quality_flag

                            self.metrics["provider_successes"][p_name] = self.metrics["provider_successes"].get(p_name, 0) + 1
                            self.metrics["grounded_descriptions"] += 1
                            self.metrics["record_provider_log"].append({
                                "tool_name": tool_name,
                                "provider": p_name,
                                "status": "SUCCESS",
                                "quality_flag": quality_flag,
                                "description": cleaned_desc
                            })
                            logger.info(f"LLM Enrichment SUCCESS for '{tool_name}' via {p_name} (Quality: {quality_flag})")
                            return record
                        else:
                            logger.warning(f"LLM output for '{tool_name}' via {p_name} failed grounding validation: {val_reason}")
                            self.metrics["ungrounded_responses"] += 1
                            self.metrics["provider_failures"][p_name] = self.metrics["provider_failures"].get(p_name, 0) + 1
                            self.metrics["fallback_events"] += 1
                    elif res.status == "UNGROUNDED":
                        logger.warning(f"LLM provider {p_name} returned status UNGROUNDED: {res.error_message}")
                        self.metrics["ungrounded_responses"] += 1
                        self.metrics["provider_failures"][p_name] = self.metrics["provider_failures"].get(p_name, 0) + 1
                        self.metrics["fallback_events"] += 1
                    elif res.status == "MALFORMED":
                        logger.warning(f"LLM output for '{tool_name}' via {p_name} was MALFORMED: {res.error_message}")
                        self.metrics["malformed_responses"] += 1
                        self.metrics["provider_failures"][p_name] = self.metrics["provider_failures"].get(p_name, 0) + 1
                        self.metrics["fallback_events"] += 1
                    else:
                        logger.warning(f"LLM provider {p_name} returned status '{res.status}': {res.error_message}")
                        self.metrics["provider_failures"][p_name] = self.metrics["provider_failures"].get(p_name, 0) + 1
                        self.metrics["fallback_events"] += 1

                except Exception as e:
                    logger.error(f"Unexpected error executing LLM provider {p_name} on '{tool_name}': {e}")
                    self.metrics["provider_failures"][p_name] = self.metrics["provider_failures"].get(p_name, 0) + 1
                    self.metrics["fallback_events"] += 1

            # All LLM providers failed or returned ungrounded descriptions -> Fallback to source
            logger.warning(f"All LLM providers failed for '{tool_name}'. Falling back to deterministic source extraction.")
            record = self._apply_deterministic_fallback(record, llm_status="FAILED_FALLBACK_TO_SOURCE")
            self.metrics["record_provider_log"].append({
                "tool_name": tool_name,
                "provider": "FALLBACK_SOURCE",
                "status": "FAILED_FALLBACK_TO_SOURCE",
                "description": record.get("description")
            })
            return record

        # Case 2: LLM enrichment not requested or no credentials configured
        status = "NOT_CONFIGURED" if enrich_llm_flag else "DISABLED"
        return self._apply_deterministic_fallback(record, llm_status=status)

    def _apply_deterministic_fallback(self, record: Dict[str, Any], llm_status: str) -> Dict[str, Any]:
        """Performs grounded deterministic source extraction fallback."""
        existing_desc = record.get("description")
        tool_name = record.get("name", "")

        record["llm_provider_used"] = "NONE"
        record["llm_enrichment_status"] = llm_status

        # Priority 1: Official website metadata
        if record.get("meta_description"):
            record["description"] = re.sub(r'^["\']|["\']$', '', record["meta_description"].strip())
            record["description_grounded"] = True
            record["description_source_type"] = "OFFICIAL_WEBSITE"
            record["description_source_url"] = record.get("official_url") or record.get("url")
            record["description_generation_method"] = "EXTRACTED_FROM_WEBSITE"
            return record

        # Priority 2: README extraction if existing desc is missing or vague
        readme = record.get("readme_content")
        is_slogan_or_vague = False
        if existing_desc:
            clean_ex = existing_desc.strip().lower()
            if len(clean_ex) < 25 or clean_ex.startswith("runs anywhere") or clean_ex in ["a tool", "ai tool"]:
                is_slogan_or_vague = True

        if readme and (not existing_desc or is_slogan_or_vague):
            readme_desc = self._extract_readme_description(readme, tool_name)
            if readme_desc and len(readme_desc) >= 20:
                record["description"] = readme_desc
                record["description_grounded"] = True
                record["description_source_type"] = "GITHUB_README"
                record["description_source_url"] = record.get("readme_url") or record.get("github_repo_url")
                record["description_generation_method"] = "EXTRACTED_FROM_README"
                return record

        # Priority 3: GitHub repository description
        if existing_desc:
            record["description"] = re.sub(r'^["\']|["\']$', '', existing_desc.strip())
            record["description_grounded"] = True
            if record.get("github_repo_url"):
                record["description_source_type"] = "GITHUB_REPOSITORY_DESCRIPTION"
                record["description_source_url"] = record.get("github_repo_url")
            elif record.get("external_evidence_url"):
                record["description_source_type"] = "EXTERNAL_EVIDENCE"
                record["description_source_url"] = record.get("external_evidence_url")
            else:
                record["description_source_type"] = record.get("discovery_source_type") or record.get("source_type", "CURATED_SEED")
                record["description_source_url"] = record.get("discovery_source_url") or record.get("source_url")
            record["description_generation_method"] = "EXTRACTED_FROM_SOURCE"
            return record

        # No evidence available
        record["description"] = None
        record["description_grounded"] = False
        record["description_source_type"] = None
        record["description_source_url"] = None
        record["description_generation_method"] = "NONE"
        if llm_status == "FAILED_FALLBACK_TO_SOURCE":
            self.metrics["records_no_usable_description"] += 1
        return record

    @staticmethod
    def _determine_source_type(res: LLMResult, evidence: EvidencePackage) -> str:
        """Determines description_source_type enum based on cited evidence."""
        if len(res.evidence_used) > 1:
            return "LLM_GROUNDED_MULTI_SOURCE"

        if res.evidence_used:
            stype = res.evidence_used[0].get("source_type", "").upper()
            if "WEBSITE" in stype:
                return "LLM_GROUNDED_OFFICIAL_WEBSITE"
            elif "README" in stype:
                return "LLM_GROUNDED_GITHUB_README"
            elif "REPOSITORY" in stype:
                return "LLM_GROUNDED_GITHUB_REPOSITORY"

        if evidence.official_website_content:
            return "LLM_GROUNDED_OFFICIAL_WEBSITE"
        elif evidence.readme_excerpt:
            return "LLM_GROUNDED_GITHUB_README"
        return "LLM_GROUNDED_GITHUB_REPOSITORY"

    @staticmethod
    def _clean_readme(readme: str) -> str:
        """Cleans README text by stripping HTML, badges, markdown formatting."""
        lines = readme.split("\n")
        substantive = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("![") or stripped.startswith("[![") or stripped.startswith("---"):
                continue
            substantive.append(stripped)
        text = " ".join(substantive)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        text = re.sub(r'[*_`]', '', text)
        return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def _extract_readme_description(readme: str, tool_name: str) -> Optional[str]:
        """Extracts the first meaningful paragraph from README content."""
        clean = LLMOrchestrator._clean_readme(readme)
        if len(clean) >= 20:
            if len(clean) > 250:
                return clean[:247] + "..."
            return clean
        return None
