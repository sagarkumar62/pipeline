import json

with open("data/exports/tools.json", "r", encoding="utf-8") as f:
    tools = json.load(f)

target_ids = [
    'tool_22722e523af215ba', 'tool_8b2c97aaa1521199', 'tool_aef70ac495a46702',
    'tool_740d362d12f4908b', 'tool_2533134dbcce5d26', 'tool_d1179244828ac03d',
    'tool_54d8589967f974ed', 'tool_e6a1d44516bb79ab', 'tool_0dc3e56862d12fef'
]

for t in tools:
    if t['id'] in target_ids:
        print(f"=== [{t['id']}] {t['name']} ===")
        print(f"Current Description: '{t.get('description')}'")
        print(f"Evidence Count: {len(t.get('evidence_sources', []))}")
        for ev in t.get('evidence_sources', []):
            snippet = ev.get("snippet", "")
            print(f"  - {ev.get('source_type')}: {ev.get('url')} (snippet_len={len(snippet)})")
            if snippet:
                print(f"    Snippet preview: {snippet[:150]}...")
