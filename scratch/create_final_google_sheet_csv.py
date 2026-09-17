import json
import csv
from pathlib import Path

TOOLS_JSON_PATH = Path("data/exports/tools.json")
FINAL_CSV_PATH = Path("data/exports/ai_orbit_tools_final_google_sheet.csv")

with open(TOOLS_JSON_PATH, "r", encoding="utf-8") as f:
    tools = json.load(f)

assert len(tools) == 50, f"Expected 50 records in tools.json, got {len(tools)}"

headers = [
    "Name",
    "Description",
    "Official Website",
    "Official Logo",
    "GitHub Repository",
    "Categories",
    "Source",
    "Source URL",
    "Record ID",
    "Website Verified",
    "Logo Verified",
    "Description Grounded"
]

rows = []
for t in tools:
    name = t.get("name", "")
    desc = t.get("description", "")
    official_url = t.get("official_url") or ""
    # CRITICAL: If official_url is null or empty, leave Official Website BLANK. DO NOT substitute GitHub repo URL!
    official_website = official_url if official_url.startswith("http") else ""
    logo_url = t.get("logo_url") or ""
    github_repo_url = t.get("github_repo_url") or ""
    
    cats = t.get("categories", [])
    categories_str = " | ".join(cats) if isinstance(cats, list) else str(cats)
    
    disc = t.get("discovery_source", {})
    if isinstance(disc, dict):
        source_name = disc.get("name", "GitHub API Search")
        source_url = disc.get("url", github_repo_url)
    else:
        source_name = str(disc) if disc else "GitHub API Search"
        source_url = github_repo_url
        
    rec_id = t.get("id", "")
    web_ver = t.get("website_verified", False)
    logo_ver = t.get("logo_verified", False)
    desc_grounded = t.get("description_grounded", False)
    
    rows.append({
        "Name": name,
        "Description": desc,
        "Official Website": official_website,
        "Official Logo": logo_url,
        "GitHub Repository": github_repo_url,
        "Categories": categories_str,
        "Source": source_name,
        "Source URL": source_url,
        "Record ID": rec_id,
        "Website Verified": web_ver,
        "Logo Verified": logo_ver,
        "Description Grounded": desc_grounded
    })

with open(FINAL_CSV_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)

print(f"Successfully generated import-ready CSV with {len(rows)} records at {FINAL_CSV_PATH}")
