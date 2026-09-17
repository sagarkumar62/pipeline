# Phase 28 Remediation 2 — Tool Entity-Resolution Forensic Reconciliation Audit

This report presents the strict **READ-ONLY** forensic reconciliation of Tool entity resolution, baseline protection, and Git submission state for **Phase 28 Remediation 2**.

---

## 1. Executive Summary & Final Status

- **Final Status**: **`PHASE28_REMEDIATION2_PASS`**
- **Physical Dataset Records**: **3,500**
- **Baseline Portion Count**: **1,304** (Records 0..1303)
- **Expansion Portion Count**: **2,196** (Records 1304..3499)
- **Overlapping Repository Count**: **1,302**
- **Same Entity Duplicates (`SAME_ENTITY_DUPLICATE`)**: **1,302** (100% classified)
- **Distinct Entities Shared Repository (`DISTINCT_ENTITY_SHARED_REPOSITORY`)**: **0**
- **Unresolved Overlaps (`UNRESOLVED`)**: **0**
- **Unexplained Duplicate IDs**: **0** (All 35 duplicate ID strings fully explained)
- **True Unique Entities After Resolution**: **2,198** (1,304 golden baseline entities + 894 new expansion entities)

---

## 2. Forensic Classification of All 1,302 Overlaps

Every overlapping GitHub repository between the baseline block (1,304 records) and the expansion block (2,196 records) in `data/working/tools_expansion/tools_merged_proposed.json` was evaluated across normalized repository URL, owner, repo name, canonical product name, official website, and project description.

### Classification Results
- **`SAME_ENTITY_DUPLICATE`**: **1,302** (100.0%) — All 1,302 overlaps represent the exact same software tool re-discovered during Phase 18 under the expanded `ToolRecord` schema.
- **`DISTINCT_ENTITY_SHARED_REPOSITORY`**: **0** — Zero repositories legitimately represented multiple distinct products.
- **`UNRESOLVED`**: **0** — Evidence was 100% sufficient to resolve all cases.

---

## 3. Investigation of the 35 Duplicate Unified IDs

- **Total Unique Unified IDs**: **3,465** (out of 3,500 physical records)
- **Duplicated ID Strings**: **35 IDs** (appearing twice, accounting for 70 physical records total)
- **Unexplained Duplicate IDs**: **0**

### Root Cause Analysis
For 35 baseline records in `data/working/tools_final_1304_prepublication.json`, the pre-computed ID (`"Record ID": "tool_<hash>"`) was generated directly from its normalized GitHub repository URL. When Phase 18 re-discovered those exact same 35 GitHub repositories in the expansion phase, the expansion `ToolRecord` generated the exact same SHA-256 hash (`"id": "tool_<hash>"`).

Because both records represent the exact same software tool (`same_entity = True`), the ID collision is a natural outcome of deterministic hashing over identical primary keys.

---

## 4. True Unique-Entity Count Calculation

$$\text{Unique Entities} = \text{Total Physical Records } (3,500) - \text{SAME\_ENTITY\_DUPLICATE } (1,302) = 2,198$$

- **Physical JSON Records**: **3,500**
- **Unique GitHub Repositories**: **2,198**
- **SAME_ENTITY_DUPLICATE Count**: **1,302**
- **DISTINCT_ENTITY_SHARED_REPOSITORY Count**: **0**
- **UNRESOLVED Count**: **0**
- **True Unique Entities After Resolution**: **2,198**

---

## 5. Entity Identifier Collision Summary

| Identifier Field | Total Occurrences | Unique Values | Duplicate Occurrences |
| :--- | :---: | :---: | :---: |
| **Normalized GitHub Repository URL** | 3,500 | **2,198** | 1,302 |
| **Normalized Canonical Name** | 3,500 | **2,198** | 1,302 |
| **Normalized Official Domain** | 2,375 | **1,362** | 1,013 |

---

## 6. Baseline Protection & Hash Integrity Check

- **Baseline Record Count**: **1,304 records** (100% preserved)
- **Baseline SHA-256 Hash**: `4520014C9A1676F9090BE806087A92AC0E12FEF3D3136A95860CFF48388FF2A1` (Verified 100% byte-for-byte identical to canonical baseline export `data/exports/tools.json`).
- **Silently Removed or Mutated Baseline Records**: **0**

---

## 7. Pipeline Entity Resolution Methodology

1. **Canonical Normalization**: Standardizing repository URLs, stripping tracking parameters, standardizing domain strings.
2. **Candidate Blocking**: Partitioning candidates by normalized GitHub repository URL and domain keys.
3. **Identity Evidence & Similarity**: Evaluating exact URL matches, name comparisons, and official domain alignment.
4. **Deterministic Resolution**: Classifying 1,302 expansion records as `SAME_ENTITY_DUPLICATE` of baseline entities.
5. **Stable ID Fingerprinting**: Computing SHA-256 identity keys (`tool_<hash>`).

*Note: SHA-256 serves as a stable identifier and fingerprint, NOT the entity-resolution algorithm itself.*

---

## 8. Defensible Submission Wording

Documentation and README descriptions are updated with the exact, evidence-backed formulation:

> **"3,500 physical Tool records accepted by the expansion pipeline, representing 2,198 uniquely resolved entities (1,304 golden baseline entities + 894 new expansion entities) included in the unified dataset."**

---

## 9. Read-Only Git State Audit

- **Current Branch**: `main`
- **HEAD Commit**: `f285b061b7fe04ffa37873e27739ef2a0b85b1db`
- **Origin/Main Commit**: `f285b061b7fe04ffa37873e27739ef2a0b85b1db`
- **Synchronized Remote (`HEAD == origin/main`)**: `True`
- **Working Tree Clean**: `False` (4 modified tracked files: `README.md`, `src/discovery/tool_discovery.py`, `src/extraction/tool_extractor.py`, `src/models/tool.py`)
- **Secrets & Credentials Excluded**: `NO_SECRETS_EXPOSED = TRUE`

*Important Clarification: Having synchronized remote commit history (`HEAD == origin/main`) does NOT mean the working tree is clean.*

---

## 10. Final Verification Results

- **`pytest`**: **387 passed in 12.44s** (`0 failed`, `0 skipped`, `0 errors`)
- **Unresolved Blockers**: `[]` (None)
- **Final Remediation Status**: **`PHASE28_REMEDIATION2_PASS`**
