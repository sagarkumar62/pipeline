# Phase 21 — MCP Dataset Expansion & Forensic Audit Report

## Executive Summary & Status
- **Status**: PHASE21_PASS_WITH_LIMITATIONS
- **Summary**: Phase 21 controlled dataset expansion completed for the MCP module. The existing 86-record golden baseline remains 100% immutable and protected. A total of 810 raw candidates were discovered from GitHub API search, resulting in 389 new high-quality MCP entities after qualification and deduplication.

---

## 1. Quantitative Accounting
1. **Status**: `PHASE21_PASS_WITH_LIMITATIONS`
2. **Baseline Count**: 86 records
3. **Raw Candidates Count**: 810 records
4. **Qualified Count**: 698 records
5. **Rejected Count (HARD_EXCLUSION)**: 106 records
6. **Review Required Count**: 6 records
7. **Baseline Duplicates Count**: 151 records
8. **Intra-Expansion Duplicates Count**: 158 records
9. **Final New MCP Count**: 389 records
10. **Proposed Total Merged Count**: 475 records (86 baseline + 389 final new)

### Mathematical Ingestion Equations
- **Equation 1**: `RAW (810) = QUALIFIED (698) + REJECTED (106) + REVIEW (6)` -> **PASSED**
- **Equation 2**: `QUALIFIED (698) = BASELINE_DUPLICATES (151) + INTRA_DUPLICATES (158) + FINAL_NEW_MCP (389)` -> **PASSED**
- **Equation 3**: `PROPOSED_TOTAL (475) = BASELINE (86) + FINAL_NEW_MCP (389)` -> **PASSED**

---

## 2. Data Sources & Provenance
11. **Actual Sources Used**:
    - GitHub MCP Search API (`topic:mcp-server`, `topic:mcp`, `topic:model-context-protocol`, `@modelcontextprotocol`, etc.)
12. **Intended but Omitted Sources**:
    - Creati.ai MCP, Official MCP Registry, Glama, Smithery, Docker Registry: Omitted due to absence of public API endpoints without anti-bot circumvention.
13. **Source Accessibility Limitations**:
    - Proprietary and scraper-protected registries were omitted to strictly enforce non-bypass rules.

---

## 3. Qualification & Entity Resolution Logic
14. **Qualification Logic**:
    - Precedence: `HARD_EXCLUSION > REVIEW_REQUIRED > QUALIFIED`.
    - Hard exclusions enforced for generic AI tools without MCP, tutorials, documentation-only repos, awesome lists, and non-MCP packages.
15. **MCP Evidence Validation**:
    - Concrete MCP evidence required (e.g. `@modelcontextprotocol/sdk` import, `mcp-server` topic, explicit MCP server implementation).
16. **Entity Resolution Logic**:
    - Priority: Exact ID -> Normalized Repository URL -> Package Identity -> Maintainer/Name Pair.

---

## 4. Verification, Descriptions, Telemetry & Metadata
17. **Website Verification Breakdown**:
    - External Official Domains: `ACCESSIBLE_UNVERIFIED`
    - GitHub Repositories: `REPOSITORY_PROVENANCE_ONLY` (GitHub repos explicitly not treated as official company website URLs)
18. **Logo Verification Breakdown**:
    - 0 verified logos (social preview cards excluded per rule).
19. **Description Provenance**:
    - 100% source-grounded from GitHub repository descriptions and README metadata.
20. **LLM Telemetry**:
    - `used`: `False` (LLM batch enrichment bypassed; all descriptions directly derived from authoritative source metadata).
21. **Category Coverage**:
    - Categories assigned based on evidenced capabilities: `Developer Tools`, `Databases`, `Search`, `Browser Automation`, `DevOps`, `APIs`, `Cloud`.
22. **MCP-Specific Metadata Coverage**:
    - Preserved available `package_name`, `mcp_type`, `tools`, `resources`, `prompts`, `open_source`.

---

## 5. Security, Tests & Protected Artifact Safety
23. **Protected Artifact Hashes**:
    - Pre- and post-run SHA-256 integrity verification passed on all protected artifacts across Tools, Repositories, Videos, Companies, MCP baseline, Models, Robots, Devices, and Agents files. `0` changed files.
24. **Security Scan Result**:
    - PASSED. No API keys, tokens, or credentials exposed in artifacts or git status.
25. **Dedicated Test Count**:
    - 7 dedicated tests in [`tests/test_mcp_expansion.py`](file:///c:/Users/hp/OneDrive/Documents/Desktop/pipeline/tests/test_mcp_expansion.py).
26. **Full Pytest Count**:
    - **344 passed** in 11.10s across the full test suite.

---

## 6. Physical Artifact Paths & Known Limitations
27. **Artifact Paths**:
    - `data/working/mcp_expansion/raw_candidates.jsonl`
    - `data/working/mcp_expansion/qualified.jsonl`
    - `data/working/mcp_expansion/rejected.jsonl`
    - `data/working/mcp_expansion/review.jsonl`
    - `data/working/mcp_expansion/baseline_duplicates.jsonl`
    - `data/working/mcp_expansion/intra_duplicates.jsonl`
    - `data/working/mcp_expansion/final_new_mcp.json`
    - `data/working/mcp_expansion/mcp_merged_proposed.json`
    - `data/working/mcp_expansion/sheet_export.csv`
    - `data/working/mcp_expansion/manifest.json`
    - `data/working/phase21_mcp_expansion_audit.json`
    - `docs/phase21-mcp-expansion.md`

28. **Known Limitations**:
    - Non-GitHub sources (Creati.ai, Glama, Smithery, Docker Registry) remain omitted due to lack of public APIs without anti-bot circumvention.
    - Proposed expansion export (`sheet_export.csv`) prepared for `MCP` worksheet tab, but NOT published to public Google Sheets.
