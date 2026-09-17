import json

with open("data/exports/tools.json", "r", encoding="utf-8") as f:
    tools = json.load(f)

detailed_strong = [t for t in tools if len(t.get('description', '')) > 100 and t.get('github_stars', 0) > 10000]
for t in detailed_strong[:5]:
    print(f"Name: {t['name']} (stars={t.get('github_stars')}, len={len(t['description'])})")
    print(f"Desc: '{t['description']}'\n")
