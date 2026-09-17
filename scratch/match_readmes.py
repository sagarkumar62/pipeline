import json

raw_readmes = {}
with open('data/raw/tools_github_api_20260917.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue
        data = json.loads(line)
        raw = data.get('raw', {})
        name = (raw.get('name') or '').lower()
        readme = raw.get('readme_content')
        if name and readme:
            raw_readmes[name] = readme

print(f"Found READMEs for {len(raw_readmes)} repositories in raw JSONL.")

with open('data/exports/tools.json', 'r', encoding='utf-8') as f:
    tools = json.load(f)

target_ids = [
    'tool_22722e523af215ba', 'tool_8b2c97aaa1521199', 'tool_aef70ac495a46702',
    'tool_740d362d12f4908b', 'tool_2533134dbcce5d26', 'tool_d1179244828ac03d',
    'tool_54d8589967f974ed', 'tool_e6a1d44516bb79ab', 'tool_0dc3e56862d12fef'
]

for t in tools:
    if t['id'] in target_ids:
        tname = t['name'].lower()
        repo_url = (t.get('github_repo_url') or '').lower()
        matched_readme = None
        for r_name, r_content in raw_readmes.items():
            if r_name == tname or r_name in repo_url:
                matched_readme = r_content
                break
        print(f"[{t['id']}] {t['name']}: matched README len = {len(matched_readme) if matched_readme else 0}")
