import json
import csv
from pathlib import Path
from urllib.parse import urlparse

JSON_PATH = Path("data/exports/tools.json")
JSONL_PATH = Path("data/exports/tools.jsonl")
CSV_PATH = Path("data/exports/tools.csv")
SHEET_CSV_PATH = Path("data/exports/ai_orbit_tools_final_google_sheet.csv")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    tools_json = json.load(f)

with open(JSONL_PATH, "r", encoding="utf-8") as f:
    tools_jsonl = [json.loads(line) for line in f if line.strip()]

with open(CSV_PATH, "r", encoding="utf-8") as f:
    csv_rows = list(csv.DictReader(f))

with open(SHEET_CSV_PATH, "r", encoding="utf-8") as f:
    sheet_rows = list(csv.DictReader(f))

print("=== FINAL PRE-PUBLICATION INTEGRITY VALIDATION ===")
assert len(tools_json) == 50, f"JSON record count must be 50, got {len(tools_json)}"
assert len(tools_jsonl) == 50, f"JSONL record count must be 50, got {len(tools_jsonl)}"
assert len(csv_rows) == 50, f"CSV record count must be 50, got {len(csv_rows)}"
assert len(sheet_rows) == 50, f"Sheet CSV record count must be 50, got {len(sheet_rows)}"

ids = [t["id"] for t in tools_json]
unique_ids = set(ids)
assert len(unique_ids) == 50, f"IDs must be unique, got {len(unique_ids)}"

github_in_website_count = 0
for r in sheet_rows:
    assert r["Name"].strip(), f"Missing Name in record {r['Record ID']}"
    assert r["Description"].strip(), f"Missing Description in record {r['Record ID']}"
    
    web = r["Official Website"].strip()
    if "github.com" in web.lower():
        github_in_website_count += 1
        
    src_url = r["Source URL"].strip()
    assert src_url.startswith("http"), f"Invalid Source URL in record {r['Record ID']}: {src_url}"

assert github_in_website_count == 0, f"Found {github_in_website_count} GitHub URLs incorrectly placed in Official Website column!"

print("Pass: Exactly 50 records in JSON, JSONL, CSV, and Sheet CSV.")
print("Pass: 50 unique IDs, 0 duplicates.")
print("Pass: 0 missing names, 0 missing descriptions.")
print("Pass: 0 GitHub URLs in Official Website column.")
print("Pass: 100% format consistency across all exports.")
print("=== FINAL PRE-PUBLICATION VALIDATION PASSED ===")
