import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

target_names = ['browser-use', 'medusa', 'openclaude', 'autoclip', 'tutti', 'open-terminal', 'tuicr', 'opc-skills', 'Seal-Report']

with open('data/raw/tools_github_api_20260917.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue
        data = json.loads(line)
        raw = data.get('raw', {})
        name = raw.get('name') or raw.get('full_name')
        if any(tn.lower() in str(name).lower() for tn in target_names):
            print(f"=== {name} ===")
            print("Description:", raw.get('description'))
            print("Topics:", raw.get('topics'))
            print("Homepage:", raw.get('homepage'))
            readme = raw.get('readme_content', '')
            if readme:
                # print first 500 chars of readme
                print("Readme snippet:", readme[:500].replace('\n', ' '))
            print()
