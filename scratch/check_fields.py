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
        print(f"[{t['id']}] {t['name']}:")
        print(f"  raw_name: {t.get('raw_name')}")
        print(f"  raw_description: {t.get('raw_description')}")
        print(f"  meta_description: {t.get('meta_description')}")
        print(f"  page_title: {t.get('page_title')}")
        print(f"  readme_content present: {bool(t.get('readme_content'))}")
        print(f"  topics: {t.get('topics')}")
        print(f"  company_name: {t.get('company_name')}")
        print(f"  all keys: {list(t.keys())}\n")
