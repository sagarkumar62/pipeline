import json
import hashlib
import pytest
import os

BASELINE_PATH = "data/exports/tools.json"
EXPECTED_BASELINE_SHA = "4520014c9a1676f9090be806087a92ac0e12fef3d3136a95860cff48388ff2a1"
ENRICHED_PATH = "data/working/tools_phase6c_enriched.json"
PREPUB_JSON_PATH = "data/working/tools_final_1304_prepublication.json"
PREPUB_CSV_PATH = "data/working/tools_final_1304_prepublication.csv"

ANANSI_RECORD_ID = "tool_8969b379ab76d73c"
ANANSI_EXPECTED_DESC = "Anansi is a self-healing web scraper that repairs broken selectors, uses browser rendering when needed, and provides an MCP server for conversational crawl workflows."
NULL_DESC_IDS = [
    "tool_2c49c8c7f351c7aa",
    "tool_aa1c8c2c233747a0",
    "tool_ed2336918237aed4",
    "tool_b827a194350de3da"
]


def get_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def test_baseline_immutability():
    sha = get_sha256(BASELINE_PATH)
    assert sha == EXPECTED_BASELINE_SHA, f"Baseline SHA mismatch! Expected {EXPECTED_BASELINE_SHA}, got {sha}"


def test_anansi_description_remediation():
    with open(ENRICHED_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)
    anansi = next((r for r in records if r["id"] == ANANSI_RECORD_ID), None)
    assert anansi is not None, "Anansi record not found"
    assert anansi["description"] == ANANSI_EXPECTED_DESC
    
    prohibited_terms = [
        "slip past", "captcha bypass", "cloudflare bypass", "datadome bypass",
        "bot detection bypass", "evade bot", "defeat captcha", "hostile sites"
    ]
    desc_lower = anansi["description"].lower()
    for term in prohibited_terms:
        assert term not in desc_lower, f"Prohibited term '{term}' found in Anansi description"


def test_category_coverage_semantics():
    with open(ENRICHED_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)
    with open(BASELINE_PATH, "r", encoding="utf-8") as f:
        baseline = json.load(f)
    baseline_ids = {r["id"] for r in baseline}

    cat_populated = sum(1 for r in records if r.get("categories") and len(r.get("categories")) > 0)
    cat_empty = sum(1 for r in records if not r.get("categories") or len(r.get("categories")) == 0)

    assert cat_populated == 50, f"Expected 50 records with categories, got {cat_populated}"
    assert cat_empty == 1254, f"Expected 1254 records with empty categories, got {cat_empty}"

    for r in records:
        if r["id"] in baseline_ids:
            assert len(r.get("categories", [])) > 0, f"Baseline record {r['id']} lost categories"
        else:
            assert len(r.get("categories", [])) == 0, f"Expansion record {r['id']} has unexpected categories"


def test_four_null_description_preservation():
    with open(ENRICHED_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)
    record_map = {r["id"]: r for r in records}
    
    for null_id in NULL_DESC_IDS:
        assert null_id in record_map, f"Null description record {null_id} missing"
        assert record_map[null_id].get("description") is None, f"Record {null_id} description is not null"


def test_total_record_count_and_deduplication():
    with open(ENRICHED_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)
    assert len(records) == 1304, f"Expected 1304 records, got {len(records)}"

    unique_ids = {r["id"] for r in records}
    unique_names = {r["name"].lower() for r in records}
    unique_repos = {r["github_repo_url"].lower() for r in records}

    assert len(unique_ids) == 1304, "Duplicate Record IDs found"
    assert len(unique_names) == 1304, "Duplicate Names found"
    assert len(unique_repos) == 1304, "Duplicate GitHub Repos found"


def test_source_url_coverage():
    with open(ENRICHED_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)
    for r in records:
        disc = r.get("discovery_source", {})
        url = disc.get("url") if isinstance(disc, dict) else None
        if not url:
            url = r.get("github_repo_url")
        assert url and url.strip(), f"Record {r['id']} missing source URL"


def test_no_anti_bot_bypass_wording():
    with open(ENRICHED_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)
    prohibited_terms = [
        "slip past", "captcha bypass", "cloudflare bypass", "datadome bypass",
        "bot detection bypass", "evade bot", "defeat captcha", "circumvent bot"
    ]
    for r in records:
        desc = r.get("description") or ""
        desc_lower = desc.lower()
        for term in prohibited_terms:
            assert term not in desc_lower, f"Prohibited anti-bot term '{term}' found in record {r['name']} ({r['id']})"
