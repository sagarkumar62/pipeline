# Phase 20 — Agents Dataset Expansion & Forensic Audit Report

## Executive Summary & Status
- **Status**: PHASE20_PASS_WITH_LIMITATIONS
- **Summary**: Phase 20 controlled dataset expansion completed for the Agents module. The existing 91-record golden baseline remains 100% immutable and protected. A total of 1,260 raw candidates were discovered from GitHub API search, resulting in 820 new high-quality agent entities after qualification and deduplication.

---

## 1. Quantitative Accounting
1. **Status**: `PHASE20_PASS_WITH_LIMITATIONS`
2. **Baseline Count**: 91 records
3. **Raw Candidates Count**: 1,260 records
4. **Qualified Count**: 1,088 records
5. **Rejected Count (HARD_EXCLUSION)**: 171 records
6. **Review Required Count**: 1 record
7. **Baseline Duplicates Count**: 136 records
8. **Intra-Expansion Duplicates Count**: 132 records
9. **Final New Agent Count**: 820 records
10. **Proposed Total Merged Count**: 911 records (91 baseline + 820 final new)

### Mathematical Ingestion Equations
- **Equation 1**: `RAW (1260) = QUALIFIED (1088) + REJECTED (171) + REVIEW (1)` -> **PASSED**
- **Equation 2**: `QUALIFIED (1088) = BASELINE_DUPLICATES (136) + INTRA_DUPLICATES (132) + FINAL_NEW_AGENTS (820)` -> **PASSED**
- **Equation 3**: `PROPOSED_TOTAL (911) = BASELINE (91) + FINAL_NEW_AGENTS (820)` -> **PASSED**

---

## 2. Data Sources & Provenance
11. **Actual Sources Used**:
    - GitHub Agent Search API (`topic:ai-agent`, `topic:autonomous-agent`, `topic:agent-framework`, `topic:coding-agent`, `topic:browser-agent`, `topic:multi-agent`, `topic:agentic-ai`, etc.)
12. **Intended but Omitted Sources**:
    - Creati.ai Agents / Futurepedia / Product Hunt: Omitted due to absence of public API interfaces and anti-scraping policy compliance.

---

## 3. Qualification & Entity Resolution Logic
13. **Qualification Logic**:
    - Precedence: `HARD_EXCLUSION > REVIEW_REQUIRED > QUALIFIED`.
    - Hard exclusions enforced for chatbots/wrappers, simple prompt libraries, tutorials, benchmark/course repos, awesome lists, and generic AI tools.
14. **Entity Resolution Logic**:
    - Priority: Exact ID -> Normalized Repository URL -> Official Domain -> Maintainer/Name Identity -> Package Identifier.
    - Baseline matches tagged separately from intra-expansion duplicates.

---

## 4. Verification, Descriptions, Telemetry & Categories
15. **Website Verification Breakdown**:
    - External Official Domains: `ACCESSIBLE_UNVERIFIED` (HTTP status accessible, identity unverified without domain ownership check)
    - GitHub Repositories: `REPOSITORY_PROVENANCE_ONLY` (GitHub repo URLs explicitly not treated as official website URLs)
16. **Logo Verification Breakdown**:
    - 0 verified logos (social preview thumbnails excluded per rule).
17. **Description Provenance**:
    - 100% source-grounded from GitHub repository descriptions and README metadata.
18. **LLM Telemetry**:
    - `used`: `False` (LLM batch enrichment bypassed; all descriptions directly derived from authoritative source metadata).
19. **Category Coverage**:
    - Categories inferred from topic tags: `Autonomous Agents`, `Coding Agents`, `Research Agents`, `Browser Agents`, `Multi-Agent Systems`, `Agent Frameworks`, `Agent Runtimes`.

---

## 5. Security, Tests & Protected Artifact Safety
20. **Protected Artifact Hashes**:
    - Pre- and post-run SHA-256 integrity verification passed on all 48 protected artifacts across Tools, Repositories, Videos, Companies, MCP, Models, Robots, Devices, and Agents baseline files. `0` changed files.
21. **Security Scan Result**:
    - PASSED. No API keys, tokens, or credentials exposed in artifacts or git status.
22. **Dedicated Test Count**:
    - 6 dedicated tests in [`tests/test_agents_expansion.py`](file:///c:/Users/hp/OneDrive/Documents/Desktop/pipeline/tests/test_agents_expansion.py).
23. **Full Pytest Count**:
    - **337 passed** in 11.67 seconds across the entire test suite.

---

## 6. Physical Artifact Paths & Known Limitations
24. **Artifact Paths**:
    - `data/working/agents_expansion/raw_candidates.jsonl`
    - `data/working/agents_expansion/qualified.jsonl`
    - `data/working/agents_expansion/rejected.jsonl`
    - `data/working/agents_expansion/review.jsonl`
    - `data/working/agents_expansion/baseline_duplicates.jsonl`
    - `data/working/agents_expansion/intra_duplicates.jsonl`
    - `data/working/agents_expansion/final_new_agents.json`
    - `data/working/agents_expansion/agents_merged_proposed.json`
    - `data/working/agents_expansion/sheet_export.csv`
    - `data/working/agents_expansion/manifest.json`
    - `data/working/phase20_agents_expansion_audit.json`
    - `docs/phase20-agents-expansion.md`

25. **Known Limitations**:
    - Non-GitHub sources (Creati.ai, Futurepedia, Product Hunt) remain omitted due to lack of public APIs without anti-bot circumvention.
    - Proposed expansion export (`sheet_export.csv`) prepared for `Agents` worksheet tab, but NOT published to public Google Sheets.
