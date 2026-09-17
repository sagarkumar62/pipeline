import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("data/exports/tools.json", "r", encoding="utf-8") as f:
    tools = json.load(f)

review_ids = [
    'tool_22722e523af215ba',  # browser-use
    'tool_e6a1d44516bb79ab',  # opc-skills
    'tool_0dc3e56862d12fef',  # Seal-Report
    'tool_d7e17d8a9f4acacc',  # modly
    'tool_abe3fb74d529db6b',  # poster-design
    'tool_cec4a984e9dac917'   # openilink-hub
]

for t in tools:
    if t['id'] in review_ids:
        print(f"=== [{t['id']}] {t['name']} ===")
        print(f"Description: '{t.get('description')}' (len={len(t.get('description', ''))})")
        print(f"Categories: {t.get('categories')}")
        print(f"Official URL: {t.get('official_url')}")
        print(f"GitHub URL: {t.get('github_repo_url')}")
        print(f"Website Verified: {t.get('website_verified')}")
        print(f"GitHub Verified: {t.get('github_repository_verified')}")
        print(f"Logo URL: {t.get('logo_url')}")
        print(f"Logo Verified: {t.get('logo_verified')}")
        print(f"Evidence Sources Count: {len(t.get('evidence_sources', []))}")
        print()
