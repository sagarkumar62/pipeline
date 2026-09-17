import json
import re
import csv
from pathlib import Path

# Paths
TOOLS_JSON = Path("data/exports/tools.json")
TOOLS_PRE_JSON = Path("data/exports/tools_pre_phase4b.json")
AUDIT_JSONL = Path("data/exports/phase4b_enrichment_audit.jsonl")

with open(TOOLS_JSON, "r", encoding="utf-8") as f:
    tools = json.load(f)

with open(TOOLS_PRE_JSON, "r", encoding="utf-8") as f:
    tools_pre = json.load(f)

with open(AUDIT_JSONL, "r", encoding="utf-8") as f:
    audit_log = [json.loads(line) for line in f if line.strip()]

pre_dict = {t["id"]: t for t in tools_pre}
audit_dict = {a["record_id"]: a for a in audit_log}

# 1. Record Count & ID Uniqueness
total_records = len(tools)
pre_records = len(tools_pre)
tool_ids = [t["id"] for t in tools]
unique_ids = set(tool_ids)
duplicate_ids = [tid for tid in set(tool_ids) if tool_ids.count(tid) > 1]
missing_ids = [tid for tid in pre_dict if tid not in unique_ids]

print("=== 1. RECORD COUNT & INTEGRITY ===")
print(f"Final records: {total_records}")
print(f"Pre-Phase4B records: {pre_records}")
print(f"Unique IDs: {len(unique_ids)}")
print(f"Duplicate IDs: {len(duplicate_ids)}")
print(f"Missing IDs: {len(missing_ids)}")

# 2. Canonical Immutability Audit
canonical_fields = [
    "id", "name", "categories", "official_url", "github_repo_url",
    "github_stars", "verification_status", "qualification_status",
    "logo_url", "logo_verified", "discovery_source", "evidence_sources"
]

canonical_records_changed = 0
canonical_fields_changed = 0
changed_details = []

for t in tools:
    tid = t["id"]
    pre_t = pre_dict.get(tid)
    if not pre_t:
        continue
    rec_changed = False
    for field in canonical_fields:
        val1 = t.get(field)
        val2 = pre_t.get(field)
        if val1 != val2:
            rec_changed = True
            canonical_fields_changed += 1
            changed_details.append((tid, field, val2, val1))
    if rec_changed:
        canonical_records_changed += 1

print("\n=== 2. CANONICAL IMMUTABILITY AUDIT ===")
print(f"canonical_records_changed: {canonical_records_changed}")
print(f"canonical_fields_changed: {canonical_fields_changed}")
if changed_details:
    print(f"Changes: {changed_details}")

# 3. Description Provenance Audit
provider_counts = {"GROQ": 0, "GEMINI": 0, "DEEPSEEK": 0, "SOURCE_FALLBACK": 0, "UNKNOWN": 0}
provenance_inconsistencies = []

for t in tools:
    provider_raw = str(t.get("llm_provider_used", "")).upper()
    enrichment_status = t.get("llm_enrichment_status")
    gen_method = str(t.get("description_generation_method", "")).upper()
    
    if "GROQ" in provider_raw:
        provider_counts["GROQ"] += 1
    elif "GEMINI" in provider_raw:
        provider_counts["GEMINI"] += 1
    elif "DEEPSEEK" in provider_raw:
        provider_counts["DEEPSEEK"] += 1
    elif provider_raw in ["NONE", "SOURCE_FALLBACK"]:
        provider_counts["SOURCE_FALLBACK"] += 1
    else:
        provider_counts["UNKNOWN"] += 1
        
    # Check impossible combinations
    if (provider_raw == "NONE" or provider_raw == "") and enrichment_status == "SUCCESS":
        provenance_inconsistencies.append((t["id"], "NONE provider but SUCCESS status"))
    if "GEMINI" in gen_method and "GROQ" in provider_raw:
        provenance_inconsistencies.append((t["id"], "gen_method LLM_GEMINI but provider GROQ"))

print("\n=== 3. PROVENANCE AUDIT ===")
print(f"Provider Distribution: {provider_counts}")
print(f"Provenance Inconsistencies: {len(provenance_inconsistencies)}")
for inc in provenance_inconsistencies:
    print(f"  - {inc}")

# 4. Description Quality Forensic Audit
MARKETING_WORDS = [
    "revolutionary", "powerful", "cutting-edge", "best", "leading",
    "innovative", "seamless", "ultimate", "game-changing", "next-gen",
    "state-of-the-art", "world-class", "unmatched", "unparalleled"
]

UNSUPPORTED_PATTERNS = [
    (r"\$\d+", "Pricing pattern"),
    (r"\b\d+\+?\s+users\b", "User count pattern"),
    (r"\bmillion\b|\bbillion\b", "Financial pattern"),
    (r"\bfounded by\b", "Founder pattern")
]

def get_sentence_count(text):
    # Normalize common abbreviations so periods in e.g., i.e., vs. don't split sentences
    cleaned = re.sub(r'\b(e\.g\.|i\.e\.|vs\.|etc\.|dr\.|inc\.|co\.|v\.)', 'abbrev', text, flags=re.I)
    sents = [s.strip() for s in re.split(r'[.!?]+', cleaned) if s.strip()]
    return len(sents)

audit_rows = []
quality_flags_count = 0
high_risk_records = []

for t in tools:
    tid = t["id"]
    name = t["name"]
    desc = t.get("description", "")
    provider = t.get("llm_provider_used", "UNKNOWN")
    grounded = t.get("description_grounded", False)
    
    sentence_count = get_sentence_count(desc)
    desc_len = len(desc)
    
    # Marketing flag
    m_words_found = [w for w in MARKETING_WORDS if re.search(r'\b' + w + r'\b', desc, re.I)]
    marketing_flag = len(m_words_found) > 0
    
    # Tautology flag
    tautology_flag = False
    if f"{name.lower()} is a {name.lower()}" in desc.lower() or "tool for tools" in desc.lower():
        tautology_flag = True
        
    # Unsupported claim flag
    unsupported_flag = False
    for pat, desc_pat in UNSUPPORTED_PATTERNS:
        if re.search(pat, desc, re.I):
            unsupported_flag = True
            
    # Specificity & Information quality heuristic
    specificity = "HIGH" if desc_len >= 80 and not marketing_flag and not tautology_flag else "MEDIUM"
    if desc_len < 60:
        specificity = "LOW"
    
    info_quality = "HIGH" if specificity in ["HIGH", "MEDIUM"] and grounded else "LOW"
    
    # Overall flags
    flags = []
    if desc_len > 350:
        flags.append("EXCEEDS_350_CHARS")
    if sentence_count > 2:
        flags.append("EXCEEDS_2_SENTENCES")
    if marketing_flag:
        flags.append(f"MARKETING_WORDS({','.join(m_words_found)})")
    if tautology_flag:
        flags.append("TAUTOLOGY")
    if unsupported_flag:
        flags.append("UNSUPPORTED_CLAIMS")
    if not grounded:
        flags.append("NOT_GROUNDED")
        
    audit_status = "PASS" if not flags else "FLAG"
    if audit_status == "FLAG":
        quality_flags_count += 1
        
    reason = "Grounded, concise, specific description." if audit_status == "PASS" else "; ".join(flags)
    
    # High risk evaluation
    evidence_sources = t.get("evidence_sources", [])
    ev_types = [ev.get("source_type") for ev in evidence_sources]
    is_readme_only = len(ev_types) == 1 and ev_types[0] == "GITHUB_README"
    is_short = desc_len < 70
    
    if is_readme_only or is_short or len(evidence_sources) == 0:
        high_risk_records.append({
            "id": tid,
            "name": name,
            "desc_len": desc_len,
            "evidence_count": len(evidence_sources),
            "readme_only": is_readme_only,
            "reason": "README_ONLY_EVIDENCE" if is_readme_only else ("SHORT_DESCRIPTION" if is_short else "SPARSE_EVIDENCE")
        })
    
    audit_rows.append({
        "record_id": tid,
        "name": name,
        "provider": provider,
        "description": desc,
        "description_length": desc_len,
        "sentence_count": sentence_count,
        "grounded": grounded,
        "specificity": specificity,
        "information_quality": info_quality,
        "marketing_flag": marketing_flag,
        "tautology_flag": tautology_flag,
        "unsupported_claim_flag": unsupported_flag,
        "final_audit_status": audit_status,
        "reason": reason
    })

print("\n=== 4. QUALITY AUDIT ===")
print(f"Total Quality Flags: {quality_flags_count}")
for r in audit_rows:
    if r["final_audit_status"] == "FLAG":
        print(f"  - [{r['record_id']}] {r['name']}: {r['reason']}")

print(f"\nHigh-Risk Records (HUMAN_REVIEW_RECOMMENDED): {len(high_risk_records)}")
for hr in high_risk_records:
    print(f"  - [{hr['id']}] {hr['name']}: {hr['reason']} (len={hr['desc_len']}, ev_count={hr['evidence_count']})")

# 5. Evidence Traceability
traceability_errors = []
for t in tools:
    tid = t["id"]
    source_type = t.get("description_source_type")
    evidence_sources = t.get("evidence_sources", [])
    
    if not evidence_sources:
        traceability_errors.append((tid, "MISSING_EVIDENCE"))
        continue
        
    for ev in evidence_sources:
        url = ev.get("url", "")
        if not url.startswith("http://") and not url.startswith("https://"):
            traceability_errors.append((tid, f"INVALID_EVIDENCE_URL({url})"))

print("\n=== 5. EVIDENCE TRACEABILITY ===")
print(f"Traceability Errors: {len(traceability_errors)}")

# Save CSV docs/phase4c_description_audit.csv
csv_path = Path("docs/phase4c_description_audit.csv")
fieldnames = [
    "record_id", "name", "provider", "description", "description_length",
    "sentence_count", "grounded", "specificity", "information_quality",
    "marketing_flag", "tautology_flag", "unsupported_claim_flag",
    "final_audit_status", "reason"
]

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(audit_rows)

print(f"\nWrote CSV audit table to {csv_path}")
