import json
import csv
from pathlib import Path

# Paths
JSON_PATH = Path("data/exports/tools.json")
JSONL_PATH = Path("data/exports/tools.jsonl")
CSV_PATH = Path("data/exports/tools.csv")
PRE_4D_PATH = Path("data/exports/tools_pre_phase4d.json")
PHASE4D_CSV_PATH = Path("docs/phase4d_description_remediation.csv")

# 1. Inspect Browser-Use Contradiction
with open(JSON_PATH, "r", encoding="utf-8") as f:
    tools_json = json.load(f)

with open(PRE_4D_PATH, "r", encoding="utf-8") as f:
    tools_pre4d = json.load(f)

tools_pre4d_dict = {t["id"]: t for t in tools_pre4d}
tools_json_dict = {t["id"]: t for t in tools_json}

phase4d_audit_dict = {}
if PHASE4D_CSV_PATH.exists():
    with open(PHASE4D_CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            phase4d_audit_dict[r["id"]] = r

bu_id = "tool_22722e523af215ba"
bu_json = tools_json_dict.get(bu_id, {})
bu_pre4d = tools_pre4d_dict.get(bu_id, {})
bu_4d_csv = phase4d_audit_dict.get(bu_id, {})

print("=== 1. BROWSER-USE CONTRADICTION AUDIT ===")
print(f"Pre-Phase 4D description: '{bu_pre4d.get('description')}' (len={len(bu_pre4d.get('description', ''))})")
print(f"Phase 4D CSV audit description: '{bu_4d_csv.get('new_description')}' (len={len(bu_4d_csv.get('new_description', ''))})")
print(f"Current tools.json description: '{bu_json.get('description')}' (len={len(bu_json.get('description', ''))})")
print(f"Does tools.json match Phase 4D audit CSV? {bu_json.get('description') == bu_4d_csv.get('new_description')}")

# 2. Phase 4D Target IDs Reconciliation Table
target_ids = [
    "tool_22722e523af215ba", "tool_8b2c97aaa1521199", "tool_aef70ac495a46702",
    "tool_740d362d12f4908b", "tool_2533134dbcce5d26", "tool_d1179244828ac03d",
    "tool_54d8589967f974ed", "tool_e6a1d44516bb79ab", "tool_0dc3e56862d12fef"
]

print("\n=== PHASE 4D -> CURRENT CANONICAL STATE RECONCILIATION ===")
mismatches_4d = 0
for tid in target_ids:
    cur = tools_json_dict.get(tid, {})
    aud = phase4d_audit_dict.get(tid, {})
    aud_new = aud.get("new_description")
    cur_desc = cur.get("description")
    match = (cur_desc == aud_new)
    if not match:
        mismatches_4d += 1
    print(f"[{tid}] {cur.get('name')}: Match={match}")
    if not match:
        print(f"  Audit CSV: '{aud_new}'")
        print(f"  Current JSON: '{cur_desc}'")

print(f"\nPhase 4D Mismatches: {mismatches_4d}")
