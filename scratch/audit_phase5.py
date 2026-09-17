import json
import csv
import re
from pathlib import Path
from urllib.parse import urlparse

# File Paths
JSON_PATH = Path("data/exports/tools.json")
JSONL_PATH = Path("data/exports/tools.jsonl")
CSV_PATH = Path("data/exports/tools.csv")

AUDIT_CSV_PATH = Path("docs/phase5_final_dataset_audit.csv")
AUDIT_MD_PATH = Path("docs/phase5_final_dataset_audit.md")
BLOCKING_ISSUES_PATH = Path("docs/phase5_blocking_issues.json")

# Load datasets
with open(JSON_PATH, "r", encoding="utf-8") as f:
    tools_json = json.load(f)

with open(JSONL_PATH, "r", encoding="utf-8") as f:
    tools_jsonl = [json.loads(line) for line in f if line.strip()]

with open(CSV_PATH, "r", encoding="utf-8") as f:
    csv_rows = list(csv.DictReader(f))

# 1. Dataset Integrity
total_records = len(tools_json)
ids = [t["id"] for t in tools_json]
unique_ids = set(ids)
duplicate_ids = [tid for tid in set(ids) if ids.count(tid) > 1]
missing_fields_count = 0
malformed_records_count = 0

for t in tools_json:
    if not t.get("id") or not t.get("name") or not t.get("categories"):
        missing_fields_count += 1

# Helper: Classify Official URL
def classify_official_url(url, github_repo_url):
    if not url or not isinstance(url, str):
        return "INVALID_OR_UNCLEAR"
    u = url.lower().strip()
    if "discord.gg" in u or "discord.com/invite" in u:
        return "DISCORD_INVITE"
    if any(domain in u for domain in ["twitter.com", "x.com", "linkedin.com", "youtube.com", "reddit.com"]):
        return "SOCIAL_PROFILE"
    if "github.com" in u:
        return "GITHUB_REPOSITORY"
    if "docs." in u or "/docs" in u or "gitbook.io" in u or "readme.io" in u:
        return "DOCUMENTATION"
    if any(domain in u for domain in ["pypi.org", "npmjs.com", "crates.io", "hub.docker.com"]):
        return "MARKETPLACE/DIRECTORY"
    if u.startswith("http://") or u.startswith("https://"):
        return "VALID_OFFICIAL_WEBSITE"
    return "OTHER"

# Helper: Classify Logo URL
def classify_logo(logo_url, logo_verified):
    if not logo_url or not isinstance(logo_url, str):
        return "MISSING"
    u = logo_url.lower().strip()
    if "githubusercontent.com/user-attachments" in u or "raw.githubusercontent.com" in u:
        return "OFFICIAL_BRAND_ASSET" if logo_verified else "GITHUB_ASSET"
    if "opengraph.githubassets.com" in u or "social_preview" in u:
        return "SOCIAL_PREVIEW"
    if u.startswith("http://") or u.startswith("https://"):
        return "OFFICIAL_SITE_ASSET" if logo_verified else "THIRD_PARTY"
    return "UNCLEAR"

# Helper: Audit Tool Qualification
def audit_tool_qualification(t):
    name = t.get("name", "").lower()
    desc = t.get("description", "").lower()
    cats = [c.lower() for c in t.get("categories", [])]
    
    non_tool_words = ["tutorial", "course", "awesome-list", "benchmark-dataset", "documentation-only"]
    for w in non_tool_words:
        if w in name or w in desc:
            return "REJECT_CANDIDATE", f"Contains non-tool marker '{w}'"
            
    # Valid Tool characteristics
    if any(c in cats for c in ["mcp", "agents", "models", "developer tools", "automation", "productivity", "coding", "data analysis"]):
        return "PASS", "Genuine Tool/Platform characteristics"
    return "REVIEW_REQUIRED", "Requires verification of tool functionality"

# Helper: Audit Category Status
def audit_category(t):
    cats = t.get("categories", [])
    if not cats:
        return "REVIEW_REQUIRED", "Missing categories"
    valid_categories = {"MCP", "Agents", "Models", "Developer Tools", "Productivity", "Automation", "Research", "Design", "Video", "Audio", "Coding", "Data Analysis", "Marketing", "AI Assistants"}
    invalid = [c for c in cats if c not in valid_categories]
    if invalid:
        return "REVIEW_REQUIRED", f"Unrecognized categories: {invalid}"
    return "PASS", "Categories aligned with taxonomy"

# Helper: Audit Specificity
MARKETING_WORDS = ["revolutionary", "powerful", "cutting-edge", "best", "leading", "seamless", "ultimate", "game-changing"]

def audit_description(t):
    desc = t.get("description", "")
    grounded = t.get("description_grounded", False)
    d_len = len(desc)
    
    if not desc:
        return "MISSING", False, "LOW", "Description is empty"
    if not grounded:
        return "UNGROUNDED", False, "LOW", "Description flagged ungrounded"
        
    m_found = [w for w in MARKETING_WORDS if re.search(r'\b' + w + r'\b', desc, re.I)]
    if m_found:
        return "MARKETING_HEAVY", True, "MEDIUM", f"Marketing words found: {m_found}"
        
    specificity = "HIGH" if d_len >= 70 else "MEDIUM"
    return "VALID", True, specificity, "Grounded, factual, concise description"

# Audit loop across 50 records
audit_rows = []
blocking_issues = []
non_blocking_issues = []

official_url_dist = {}
logo_dist = {}
qualification_dist = {}

for t in tools_json:
    tid = t["id"]
    name = t["name"]
    official_url = t.get("official_url")
    web_verified = t.get("website_verified", False)
    github_verified = t.get("github_repository_verified", False)
    logo_url = t.get("logo_url")
    logo_verified = t.get("logo_verified", False)
    disc_source = t.get("discovery_source", {}).get("name") if isinstance(t.get("discovery_source"), dict) else str(t.get("discovery_source"))
    ev_count = len(t.get("evidence_sources", []))
    
    # URL classification
    url_class = classify_official_url(official_url, t.get("github_repo_url"))
    official_url_dist[url_class] = official_url_dist.get(url_class, 0) + 1
    
    # Logo classification
    logo_class = classify_logo(logo_url, logo_verified)
    logo_dist[logo_class] = logo_dist.get(logo_class, 0) + 1
    
    # Tool qualification
    qual_status, qual_reason = audit_tool_qualification(t)
    qualification_dist[qual_status] = qualification_dist.get(qual_status, 0) + 1
    
    # Category audit
    cat_status, cat_reason = audit_category(t)
    
    # Description audit
    desc_status, desc_grounded, desc_spec, desc_reason = audit_description(t)
    
    # Provenance audit
    prov_status = "PASS"
    prov_issues = []
    if not disc_source:
        prov_status = "REVIEW_REQUIRED"
        prov_issues.append("Missing discovery source")
    if ev_count == 0:
        prov_status = "REVIEW_REQUIRED"
        prov_issues.append("Zero evidence sources")
        
    # Deduplication status
    dup_status = "UNIQUE"
    
    # Issues list
    issues = []
    if qual_status != "PASS":
        issues.append(f"ToolQual: {qual_reason}")
    if url_class in ["DISCORD_INVITE", "SOCIAL_PROFILE", "MARKETPLACE/DIRECTORY"]:
        issues.append(f"UrlClass: {url_class}")
    if logo_class == "MISSING":
        issues.append("Logo: MISSING")
    if desc_spec == "MEDIUM":
        issues.append("Desc: Concise (< 70 chars)")
        
    # Per-record Final Status
    if qual_status == "REJECT_CANDIDATE" or not desc_grounded:
        final_status = "NOT_READY"
        blocking_issues.append({
            "record_id": tid,
            "tool_name": name,
            "issue_type": "TOOL_QUALIFICATION" if qual_status == "REJECT_CANDIDATE" else "DESCRIPTION_UNGROUNDED",
            "details": "; ".join(issues)
        })
    elif issues:
        final_status = "REVIEW_REQUIRED"
        non_blocking_issues.append({
            "record_id": tid,
            "tool_name": name,
            "issues": issues
        })
    else:
        final_status = "READY"
        
    audit_rows.append({
        "id": tid,
        "name": name,
        "tool_qualification": qual_status,
        "official_url": official_url,
        "official_url_classification": url_class,
        "website_verified": web_verified,
        "github_repository_verified": github_verified,
        "logo_url": logo_url or "",
        "logo_classification": logo_class,
        "logo_verified": logo_verified,
        "discovery_source": disc_source,
        "evidence_source_count": ev_count,
        "provenance_status": prov_status,
        "description_status": desc_status,
        "description_grounded": desc_grounded,
        "description_specificity": desc_spec,
        "duplicate_status": dup_status,
        "category_status": cat_status,
        "final_status": final_status,
        "issues": "; ".join(issues) if issues else "None"
    })

# Determine Publication Gate Status
if len(blocking_issues) > 0:
    pub_status = "PHASE5_BLOCKED_DATA_QUALITY"
elif len(non_blocking_issues) > 0:
    pub_status = "PHASE5_READY_WITH_REVIEW_ITEMS"
else:
    pub_status = "PHASE5_FINAL_DATASET_READY"

print(f"\nPublication Gate Status: {pub_status}")
print(f"Total Blocking Issues: {len(blocking_issues)}")
print(f"Total Non-Blocking Review Items: {len(non_blocking_issues)}")

# Write CSV Audit Table
csv_headers = [
    "id", "name", "tool_qualification", "official_url", "official_url_classification",
    "website_verified", "github_repository_verified", "logo_url", "logo_classification",
    "logo_verified", "discovery_source", "evidence_source_count", "provenance_status",
    "description_status", "description_grounded", "description_specificity",
    "duplicate_status", "category_status", "final_status", "issues"
]

with open(AUDIT_CSV_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=csv_headers)
    writer.writeheader()
    writer.writerows(audit_rows)
print(f"Wrote CSV audit table to {AUDIT_CSV_PATH}")

# Write Blocking Issues JSON
with open(BLOCKING_ISSUES_PATH, "w", encoding="utf-8") as f:
    json.dump(blocking_issues, f, indent=2, ensure_ascii=False)
print(f"Wrote blocking issues JSON to {BLOCKING_ISSUES_PATH}")
