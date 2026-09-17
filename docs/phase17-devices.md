# Phase 17 — Devices Module Implementation & Forensic Audit Report

## 1. Scope
- **Module**: Devices
- **Long-term Target**: 1,000 entities
- **Phase 17 Target Sample**: 100–200 raw candidates (Collected: 120)
- **Status**: PHASE17_PASS_WITH_LIMITATIONS (Module functional; GitHub API search utilized, live vendor web scraping restricted)

## 2. Architecture & Created Files
- `src/models/device.py` — `DeviceRecord(BaseEntity)` with `entity_type = "device"`
- `src/discovery/device_discovery.py` — `DevicesAdapter` for GitHub AI Hardware Search
- `src/extraction/device_extractor.py` — `DeviceExtractor` for structured hardware facts
- `src/qualification/device_qualifier.py` — `DeviceQualifier` with `HARD_EXCLUSION > REVIEW_REQUIRED > QUALIFIED`
- `src/deduplication/device_resolver.py` — `DeviceDeduplicationResolver` maintaining distinct product identity
- `data/working/devices/devices_sheet_export.csv` — Sheet-ready export formatted for the `Devices` tab

## 3. Sources
- **Intended Sources**: GitHub AI Hardware Repositories, Hardware Vendor Portals, Edge AI Registries.
- **Actual Sources Used**: GitHub AI Hardware & Edge Devices Search (API).
- **Inaccessible Sources**: Vendor authentication portals and proprietary DevKit databases lacking public API interfaces.

## 4. Ingestion Accounting Reconciliation
- **Raw Candidates**: 120
- **Qualified Candidates**: 107
- **Hard Exclusions (Rejected)**: 12
- **Review Required**: 1
- **Duplicates Resolved**: 0
- **Final Unique Records**: 107

### Accounting Verification
1. `RAW (120) = QUALIFIED (107) + REJECTED (12) + REVIEW (1)` -> **MATCH**
2. `QUALIFIED (107) = FINAL (107) + DUPLICATES (0)` -> **MATCH**

## 5. Verification & Logo Semantics
- **Website Verification**: `ACCESSIBLE_UNVERIFIED` for non-GitHub official sites; `REPOSITORY_PROVENANCE_ONLY` for repo-only items.
- **Logo Verification**: 0 verified logos (unverified social preview thumbnails excluded per project policy).

## 6. Sheet Export
- **Intended Worksheet Name**: `Devices`
- **Export Location**: `data/working/devices/devices_sheet_export.csv`
- **Rows**: 107
- **Columns**: 23
- **Google Sheets Modification**: CONFIRMED NOT MODIFIED. Public spreadsheet was left untouched.

## 7. Protected Data Safety
- 40 protected baseline files (Tools, Repositories, MCP, Agents, Models, Companies, Robots) verified with 100% SHA-256 byte-for-byte identity pre- and post-phase.
