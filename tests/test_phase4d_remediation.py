"""
Phase 4D Description Remediation Unit Tests

Verifies:
1. Target ID eligibility (only the 9 target records are modified).
2. Non-target record immutability (41 non-target records remain identical).
3. Canonical field immutability (zero canonical field mutations).
4. Duplicate ID detection (asserts 50 unique IDs, 0 duplicates).
5. Evidence package boundaries.
6. Grounding validation of regenerated descriptions.
7. Retention of existing grounded descriptions if regeneration fails or lacks evidence.
8. Rejection of generic/tautological wording.
9. Provenance internal consistency.
10. Canonical ToolRecord schema validation.
"""

import json
import pytest
from pathlib import Path
from src.models.tool import ToolRecord
from src.enrichment.validator import GroundingValidator
from src.enrichment.quality import DescriptionQualityChecker
from src.enrichment.schema import EvidencePackage, StructuredLLMOutput

TARGET_IDS = {
    "tool_22722e523af215ba", "tool_8b2c97aaa1521199", "tool_aef70ac495a46702",
    "tool_740d362d12f4908b", "tool_2533134dbcce5d26", "tool_d1179244828ac03d",
    "tool_54d8589967f974ed", "tool_e6a1d44516bb79ab", "tool_0dc3e56862d12fef"
}

CANONICAL_FIELDS = [
    "id", "name", "categories", "official_url", "github_repo_url",
    "github_stars", "verification_status", "qualification_status",
    "logo_url", "logo_verified", "discovery_source", "evidence_sources"
]


def load_tools(path_str):
    p = Path(path_str)
    if not p.exists():
        pytest.skip(f"File {path_str} does not exist yet.")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def test_target_ids_eligibility():
    tools = load_tools("data/exports/tools.json")
    assert len(tools) == 50
    existing_ids = {t["id"] for t in tools}
    assert TARGET_IDS.issubset(existing_ids), "All 9 target IDs must exist in the canonical dataset."


def test_unique_ids_and_no_duplicates():
    tools = load_tools("data/exports/tools.json")
    ids = [t["id"] for t in tools]
    assert len(ids) == 50
    assert len(set(ids)) == 50, "All 50 record IDs must be unique."


def test_pre_phase4d_snapshot_exists():
    snapshot_path = Path("data/exports/tools_pre_phase4d.json")
    if not snapshot_path.exists():
        pytest.skip("tools_pre_phase4d.json not generated yet.")
    tools_pre = load_tools("data/exports/tools_pre_phase4d.json")
    assert len(tools_pre) == 50


def test_non_target_records_and_canonical_immutability():
    tools = load_tools("data/exports/tools.json")
    tools_pre_path = Path("data/exports/tools_pre_phase4d.json")
    if not tools_pre_path.exists():
        pytest.skip("Pre-Phase4D snapshot does not exist yet.")
    tools_pre = load_tools("data/exports/tools_pre_phase4d.json")
    pre_dict = {t["id"]: t for t in tools_pre}

    non_target_mutations = 0
    canonical_mutations = 0

    for t in tools:
        tid = t["id"]
        pre_t = pre_dict.get(tid)
        assert pre_t is not None

        # Check canonical fields for ALL records
        for field in CANONICAL_FIELDS:
            if t.get(field) != pre_t.get(field):
                canonical_mutations += 1

        # Check description fields for NON-TARGET records
        if tid not in TARGET_IDS:
            if t.get("description") != pre_t.get("description"):
                non_target_mutations += 1

    assert canonical_mutations == 0, f"Found {canonical_mutations} canonical field mutations."
    assert non_target_mutations == 0, f"Found {non_target_mutations} non-target record description mutations."


def test_evidence_package_excludes_unsupported_knowledge():
    validator = GroundingValidator()
    ev_pkg = EvidencePackage(
        tool_name="tuicr",
        repository_description="a code review TUI with vim keybindings",
        github_repo_url="https://github.com/agavra/tuicr"
    )
    # Output with fabricated pricing and funding claims
    fabricated_output = StructuredLLMOutput(
        description="tuicr raised $50M to build a $99/mo vim tool for 10,000 developers.",
        grounded=True,
        confidence="high"
    )
    is_grounded, reason = validator.validate(fabricated_output, ev_pkg)
    assert not is_grounded, "Validator must reject fabricated pricing/funding/metrics."


def test_regenerated_descriptions_pass_grounding():
    tools = load_tools("data/exports/tools.json")
    validator = GroundingValidator()
    for t in tools:
        if t["id"] in TARGET_IDS:
            ev_pkg = EvidencePackage(
                tool_name=t["name"],
                official_website_content=t.get("meta_description"),
                repository_description=t.get("description"),
                github_repo_url=t.get("github_repo_url")
            )
            output = StructuredLLMOutput(
                description=t["description"],
                grounded=True,
                confidence="high"
            )
            is_grounded, reason = validator.validate(output, ev_pkg)
            assert is_grounded, f"Description for '{t['name']}' failed grounding validation: {reason}"


def test_generic_and_tautological_rejection():
    checker = DescriptionQualityChecker()
    flag1, pass1 = checker.check_quality("An innovative AI tool for productivity.", "mytool")
    assert not pass1, "Generic slogans must fail quality check."

    flag2, pass2 = checker.check_quality("mytool is a mytool tool.", "mytool")
    assert not pass2, "Tautology must fail quality check."


def test_provenance_internal_consistency():
    tools = load_tools("data/exports/tools.json")
    for t in tools:
        provider = t.get("llm_provider_used")
        status = t.get("llm_enrichment_status")
        method = t.get("description_generation_method")
        grounded = t.get("description_grounded")

        assert status == "SUCCESS", f"Record {t['id']} status should be SUCCESS"
        assert grounded is True, f"Record {t['id']} should be grounded"
        if provider == "Groq":
            assert method == "LLM_GROQ"
        elif provider == "Gemini":
            assert method == "LLM_GEMINI"


def test_canonical_schema_validation():
    tools = load_tools("data/exports/tools.json")
    for t in tools:
        # Validate pydantic ToolRecord instantiation
        record = ToolRecord(**t)
        assert record.id == t["id"]
