import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

TOOLS_PATH = Path("data/exports/tools.json")
PRE_PATH = Path("data/exports/tools_pre_phase4d.json")

with open(TOOLS_PATH, "r", encoding="utf-8") as f:
    tools = json.load(f)

with open(PRE_PATH, "r", encoding="utf-8") as f:
    tools_pre = json.load(f)

assert len(tools) == 50, f"Expected 50 records, found {len(tools)}"
assert len(tools_pre) == 50, f"Expected 50 pre-records, found {len(tools_pre)}"

target_ids = {
    'tool_22722e523af215ba', 'tool_8b2c97aaa1521199', 'tool_aef70ac495a46702',
    'tool_740d362d12f4908b', 'tool_2533134dbcce5d26', 'tool_d1179244828ac03d',
    'tool_54d8589967f974ed', 'tool_e6a1d44516bb79ab', 'tool_0dc3e56862d12fef'
}

canonical_fields = [
    "id", "name", "categories", "official_url", "github_repo_url",
    "github_stars", "verification_status", "qualification_status",
    "logo_url", "logo_verified", "discovery_source", "evidence_sources"
]

pre_dict = {t["id"]: t for t in tools_pre}
canonical_field_changes = 0
non_target_description_changes = 0
remediated_count = 0
retained_count = 0

print("=== VERIFYING ALL 9 TARGET RECORDS ===")
for t in tools:
    tid = t["id"]
    pre_t = pre_dict[tid]
    
    # Check canonical fields
    for field in canonical_fields:
        if t.get(field) != pre_t.get(field):
            print(f"MUTATION FAIL in {tid} field {field}: {pre_t.get(field)} -> {t.get(field)}")
            canonical_field_changes += 1
            
    # Check non-target description
    if tid not in target_ids:
        if t.get("description") != pre_t.get("description"):
            print(f"NON-TARGET FAIL in {tid} description changed!")
            non_target_description_changes += 1
    else:
        old_desc = pre_t.get("description")
        new_desc = t.get("description")
        if old_desc != new_desc:
            remediated_count += 1
            print(f"[{tid}] {t['name']} REMEDIATED ({len(old_desc)} -> {len(new_desc)} chars):")
            print(f"  Old: '{old_desc}'")
            print(f"  New: '{new_desc}'\n")
        else:
            retained_count += 1
            print(f"[{tid}] {t['name']} RETAINED ({len(old_desc)} chars):")
            print(f"  Desc: '{old_desc}'\n")

print("=== VERIFICATION SUMMARY ===")
print(f"Total records: {len(tools)}")
print(f"Target records reviewed: {len(target_ids)}")
print(f"Remediated (Modified): {remediated_count}")
print(f"Retained (Unchanged): {retained_count}")
print(f"Canonical Field Changes: {canonical_field_changes}")
print(f"Non-Target Description Changes: {non_target_description_changes}")
