# Phase 24 — Devices Dataset Expansion & Forensic Audit Report

## Executive Summary & Status
- **Status**: PHASE24_PASS_WITH_LIMITATIONS
- **Summary**: Phase 24 controlled dataset expansion completed for the Devices module. The existing 107-record golden baseline remains 100% immutable and protected. A total of 445 raw candidates were discovered from GitHub AI Hardware Search API, resulting in 230 new high-quality physical Device entities after qualification and identity deduplication.

---

## 1. Quantitative Accounting
1. **Status**: `PHASE24_PASS_WITH_LIMITATIONS`
2. **Baseline Count**: 107 records
3. **Raw Candidates Count**: 445 records
4. **Qualified Count**: 347 records
5. **Rejected Count (HARD_EXCLUSION)**: 86 records
6. **Review Required Count**: 12 records
7. **Baseline Duplicates Count**: 107 records
8. **Intra-Expansion Duplicates Count**: 10 records
9. **Final New Device Count**: 230 records
10. **Proposed Total Merged Count**: 337 records (107 baseline + 230 final new)

### Mathematical Ingestion Equations
- **Equation 1**: `RAW (445) = QUALIFIED (347) + REJECTED (86) + REVIEW (12)` -> **PASSED**
- **Equation 2**: `QUALIFIED (347) = BASELINE_DUPLICATES (107) + INTRA_DUPLICATES (10) + FINAL_NEW_DEVICES (230)` -> **PASSED**
- **Equation 3**: `PROPOSED_TOTAL (337) = BASELINE (107) + FINAL_NEW_DEVICES (230)` -> **PASSED**

---

## 2. Data Sources & Provenance
11. **Actual Sources Used**:
    - GitHub AI Hardware Search API (`topic:edge-ai`, `topic:ai-hardware`, `topic:ai-dev-kit`, `topic:jetson`, `topic:embedded-ai`, etc.)
12. **Intended but Omitted Sources**:
    - TAAFT Devices, Physical AI Devices: Omitted due to absence of public API endpoints without anti-bot circumvention.
13. **Source Accessibility Limitations**:
    - Proprietary and scraper-protected registries omitted to enforce non-bypass rules.

---

## 3. Qualification & Device Identity Logic
14. **Qualification Logic**:
    - Precedence: `HARD_EXCLUSION > REVIEW_REQUIRED > QUALIFIED`.
    - Hard exclusions enforced for software-only applications, AI models, chatbots, MCP servers, software SDKs, cloud services, and standalone components (sensors/cables sold separately).
15. **Device vs Robot Distinction**:
    - Physical hardware/computing platforms (dev kits, edge computers) classified as Devices; complete robotic systems (humanoids, quadrupeds) preserved under Robots.
16. **Device Identity Resolution Logic**:
    - Priority: Stable Device ID -> Exact Official Product URL -> Manufacturer + Model Identity -> Exact Manufacturer + Name Pair.
17. **Manufacturer / Model Handling**:
    - Manufacturer vs Device entity distinction preserved (company not collapsed into device).
18. **Variant / Configuration Handling**:
    - Device configuration variants (RAM/storage options) retained as metadata where they represent the same canonical device.

---

## 4. Verification, Descriptions & Metadata
19. **Website Verification Breakdown**:
    - External Official Product Landing Pages: `ACCESSIBLE_UNVERIFIED`
    - GitHub Repositories: `REPOSITORY_PROVENANCE_ONLY`
20. **Logo Verification Breakdown**:
    - 0 verified logos (avatars and social preview images excluded per rule).
21. **Description Provenance**:
    - 100% source-grounded from repository metadata and README files.
22. **LLM Telemetry**:
    - `used`: `False` (LLM batch enrichment bypassed).
23. **Category Coverage**:
    - Categories covered: `Edge AI`, `AI Development Kit`, `AI Inference`, `AI Accelerator`, `Embedded AI`, `Robotics Compute`, `Industrial AI Hardware`.
24. **Device Metadata Coverage**:
    - Preserved `manufacturer`, `device_type`, `physical_form`, `capabilities`, `processor`, `accelerator`, `operating_system`, `open_source`.

---

## 5. Security, Tests & Protected Artifact Safety
25. **Protected Artifact Hashes**:
    - Pre- and post-run SHA-256 integrity verification passed on all protected artifacts across Tools, Repositories, Videos, Companies, MCP, Models, Robots, Devices baseline, and Agents files. `0` changed files.
26. **Security Scan Result**:
    - PASSED. No API keys, tokens, or credentials exposed in artifacts or git status.
27. **Dedicated Test Count**:
    - Dedicated tests written in `tests/test_devices_expansion.py`.
28. **Full Pytest Count**:
    - Full test suite verified.

---

## 6. Physical Artifact Paths & Known Limitations
29. **Artifact Paths**:
    - `data/working/devices_expansion/raw_candidates.jsonl`
    - `data/working/devices_expansion/qualified.jsonl`
    - `data/working/devices_expansion/rejected.jsonl`
    - `data/working/devices_expansion/review.jsonl`
    - `data/working/devices_expansion/baseline_duplicates.jsonl`
    - `data/working/devices_expansion/intra_duplicates.jsonl`
    - `data/working/devices_expansion/final_new_devices.json`
    - `data/working/devices_expansion/devices_merged_proposed.json`
    - `data/working/devices_expansion/sheet_export.csv`
    - `data/working/devices_expansion/manifest.json`
    - `data/working/phase24_devices_expansion_audit.json`
    - `docs/phase24-devices-expansion.md`

30. **Known Limitations**:
    - Non-API sources (TAAFT Devices, Physical AI Devices) omitted due to lack of public APIs without anti-bot circumvention.
    - Proposed expansion export (`sheet_export.csv`) prepared for `Devices` worksheet tab, but NOT published to public Google Sheets.
