import json

with open("data/exports/tools.json", "r", encoding="utf-8") as f:
    tools = json.load(f)

# Group 1: 5 strongest evidence records (website verified + repo verified + stars > 1000 + 2+ evidence sources)
strong = [t for t in tools if t.get('website_verified') and t.get('github_stars', 0) > 1000 and len(t.get('evidence_sources', [])) >= 2]
strong = sorted(strong, key=lambda x: x.get('github_stars', 0), reverse=True)[:5]

# Group 2: 5 sparse/short description or README heavy records
short_ids = ['tool_22722e523af215ba', 'tool_8b2c97aaa1521199', 'tool_aef70ac495a46702', 'tool_740d362d12f4908b', 'tool_2533134dbcce5d26']
sparse = [t for t in tools if t['id'] in short_ids]

# Group 3: 5 unusual/ambiguous/niche records (e.g. MCP, Terminal, unusual categories)
unusual_ids = ['tool_d1179244828ac03d', 'tool_54d8589967f974ed', 'tool_e6a1d44516bb79ab', 'tool_0dc3e56862d12fef', 'tool_dee87fe28e66478b']
unusual = [t for t in tools if t['id'] in unusual_ids]

print("=== GROUP 1: STRONGEST EVIDENCE RECORDS ===")
for t in strong:
    ev_types = [e.get('source_type') for e in t.get('evidence_sources', [])]
    print(f"- {t['name']} (stars={t.get('github_stars')}, ev={ev_types})")
    print(f"  Desc: '{t['description']}'")

print("\n=== GROUP 2: SPARSE/README HEAVY RECORDS ===")
for t in sparse:
    ev_types = [e.get('source_type') for e in t.get('evidence_sources', [])]
    print(f"- {t['name']} (id={t['id']}, ev={ev_types})")
    print(f"  Desc: '{t['description']}'")

print("\n=== GROUP 3: UNUSUAL / AMBIGUOUS RECORDS ===")
for t in unusual:
    ev_types = [e.get('source_type') for e in t.get('evidence_sources', [])]
    print(f"- {t['name']} (id={t['id']}, ev={ev_types})")
    print(f"  Desc: '{t['description']}'")
