import json

with open("data/exports/tools.json", "r", encoding="utf-8") as f:
    tools = json.load(f)

print("=== OPENCODEX (3 sentences) ===")
for t in tools:
    if t["id"] == "tool_dee87fe28e66478b":
        print(f"Name: {t['name']}")
        print(f"Description: {t['description']}")
        print(f"Length: {len(t['description'])}")

print("\n=== SHORT DESCRIPTIONS (< 70 CHARS) ===")
short_ids = [
    'tool_22722e523af215ba', 'tool_8b2c97aaa1521199', 'tool_aef70ac495a46702',
    'tool_740d362d12f4908b', 'tool_2533134dbcce5d26', 'tool_d1179244828ac03d',
    'tool_54d8589967f974ed', 'tool_e6a1d44516bb79ab', 'tool_0dc3e56862d12fef'
]

for t in tools:
    if t["id"] in short_ids:
        print(f"[{t['id']}] {t['name']}: '{t['description']}' (len={len(t['description'])})")
