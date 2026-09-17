# Phase 19 — Companies Dataset Expansion & Forensic Audit Report

## 1. Scope
- **Module**: Companies (Expansion Batch)
- **Long-term Target**: 10,000 entities
- **Golden Protected Baseline**: 107 records (100% Immutable)
- **Phase 19 Raw Candidates Discovered**: 458
- **Final New Validated Companies**: 402 records
- **Proposed Total Companies Count**: 509 records
- **Status**: PHASE19_PASS_WITH_LIMITATIONS (Pipeline scales cleanly; baseline untouched; Crunchbase/Tracxn/TAAFT lack public APIs)

## 2. Ingestion Accounting Reconciliation
- **Raw Candidates**: 458
- **Qualified Candidates**: 452
- **Hard Exclusions (Rejected)**: 6
- **Review Required**: 0
- **Baseline Duplicates**: 50
- **Intra-Expansion Duplicates**: 0
- **Final New Companies**: 402

### Accounting Verification
1. `RAW (458) = QUALIFIED (452) + REJECTED (6) + REVIEW (0)` -> **MATCH**
2. `QUALIFIED (452) = BASELINE_DUPLICATES (50) + INTRA_DUPLICATES (0) + FINAL_NEW_COMPANIES (402)` -> **MATCH**

## 3. Sources
- **Intended Sources**: TAAFT, Crunchbase, Tracxn, Accelerators, Company Websites, GitHub.
- **Actual Sources Used**: GitHub Organizations API.
- **Inaccessible Sources**: Crunchbase, Tracxn, TAAFT (Lacking public APIs / paywall restricted).

## 4. Verification & Logo Semantics
- **Website Verification**: `ACCESSIBLE_UNVERIFIED` for official domains; `REPOSITORY_PROVENANCE_ONLY` for github org urls.
- **Logo Verification**: 0 verified logos (unverified thumbnails excluded).

## 5. Sheet Export & Proposed Merged Dataset
- **Intended Worksheet Name**: `Companies`
- **Sheet Export Location**: `data/working/companies_expansion/sheet_export.csv` (402 new rows)
- **Proposed Merged Location**: `data/working/companies_expansion/companies_merged_proposed.json` (509 total rows)
- **Public Google Spreadsheet & Frozen Exports**: CONFIRMED NOT MODIFIED.

## 6. Protected Data Safety
- 47 protected baseline files verified with 100% SHA-256 byte-for-byte identity pre- and post-phase.
