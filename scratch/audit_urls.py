import json
import csv
from pathlib import Path

with open("data/exports/tools.json", "r", encoding="utf-8") as f:
    tools = json.load(f)

def classify_url(url, github_repo_url):
    if not url or not isinstance(url, str):
        return "MISSING"
    u = url.lower().strip()
    if "discord.gg" in u or "discord.com/invite" in u:
        return "DISCORD_INVITE"
    if any(d in u for d in ["twitter.com", "x.com", "linkedin.com", "youtube.com", "reddit.com"]):
        return "SOCIAL_PROFILE"
    if "github.com" in u:
        return "GITHUB_REPOSITORY"
    if "docs." in u or "/docs" in u or "gitbook.io" in u or "readme.io" in u:
        return "DOCUMENTATION"
    if any(d in u for d in ["pypi.org", "npmjs.com", "crates.io", "hub.docker.com"]):
        return "PACKAGE_REGISTRY"
    if any(d in u for d in ["trendshift.io", "producthunt.com", "ycombinator.com"]):
        return "DIRECTORY_OR_AGGREGATOR"
    if u.startswith("http://") or u.startswith("https://"):
        return "OFFICIAL_EXTERNAL_WEBSITE"
    return "OTHER"

counts = {}
suspicious = []

for t in tools:
    tid = t["id"]
    name = t["name"]
    url = t.get("official_url")
    gh = t.get("github_repo_url")
    cls = classify_url(url, gh)
    counts[cls] = counts.get(cls, 0) + 1
    
    if cls != "OFFICIAL_EXTERNAL_WEBSITE":
        suspicious.append({
            "id": tid,
            "name": name,
            "official_url": url,
            "github_repo_url": gh,
            "classification": cls
        })

print("=== OFFICIAL URL CLASSIFICATION BREAKDOWN ===")
for k, v in counts.items():
    print(f"  {k}: {v}")

print(f"\nSuspicious / Non-External-Website Official URLs: {len(suspicious)}")
for s in suspicious:
    print(f"  - [{s['id']}] {s['name']}: {s['official_url']} -> {s['classification']}")
