# Phase 15 — Companies Module Implementation Report
**AI Orbit Data Ingestion Pipeline**

---

## 1. Executive Summary

Phase 15 establishes the **Companies Module** as an independent, production-grade entity ingestion pipeline within the AI Orbit multi-module architecture. The implementation builds upon the `BaseEntity` root schema, extending it with the `CompanyRecord` model (`src/models/company.py`), `CompanyAdapter` discovery adapter (`src/discovery/company_discovery.py`), `CompanyExtractor` (`src/extraction/company_extractor.py`), `CompanyQualifier` (`src/qualification/company_qualifier.py`), and `CompanyDeduplicationResolver` (`src/deduplication/company_resolver.py`).

All Phase 15 artifacts are stored strictly isolated under `data/working/companies/`. The protected Tools dataset (1,304 records), Repositories dataset (88 records), MCP dataset (86 records), Agents dataset (91 records), and Models dataset (102 records) remain 100% byte-for-byte intact and cryptographically verified across 28 protected files.

Final Phase 15 Status: **`PHASE15_PASS_WITH_LIMITATIONS`**

---

## 2. Protected Data Safety Audit

Pre-phase and post-phase SHA-256 cryptographic hashes were recorded for all 28 protected artifacts across Tools, Repositories, MCP, Agents, and Models modules:

| Protected Artifact Path | Expected / Pre-Phase SHA-256 | Post-Phase SHA-256 | Integrity Status |
|---|---|---|---|
| `data/exports/tools.json` | `4520014C9A1676F9090BE806087A92AC0E12FEF3D3136A95860CFF48388FF2A1` | `4520014C9A1676F9090BE806087A92AC0E12FEF3D3136A95860CFF48388FF2A1` | **MATCH (100%)** |
| `data/exports/tools.csv` | `2483F4F19906137B5F3EF871BDDC462374671683DEE1A7A4BF9CD67C357600B7` | `2483F4F19906137B5F3EF871BDDC462374671683DEE1A7A4BF9CD67C357600B7` | **MATCH (100%)** |
| `data/validated/tools.jsonl` | `991065F2BF403DA51B71167F24757012E3F85CBB304EC41ABF041485955161E5` | `991065F2BF403DA51B71167F24757012E3F85CBB304EC41ABF041485955161E5` | **MATCH (100%)** |
| `data/working/baseline_manifest.json` | `40B5DAAC7E4AB5CF5A1DC404D3820798D6F227A2C8883993E448919722AE25C0` | `40B5DAAC7E4AB5CF5A1DC404D3820798D6F227A2C8883993E448919722AE25C0` | **MATCH (100%)** |
| `data/working/repositories/repositories_final.json` | `176D5DEEEC8063FC4684C058B5E758649E57375ACE6AB5ADA05A4ECE43FB8465` | `176D5DEEEC8063FC4684C058B5E758649E57375ACE6AB5ADA05A4ECE43FB8465` | **MATCH (100%)** |
| `data/working/mcp/mcp_final.json` | `CED0BF7AE869ACC54403C0453A1A12CF097131D6D5CB438BEA36216822A9216B` | `CED0BF7AE869ACC54403C0453A1A12CF097131D6D5CB438BEA36216822A9216B` | **MATCH (100%)** |
| `data/working/agents/agents_final.json` | `B27609EA151951A97445CA5CFDF54C58F22B223D87808B466BA505BC6E00DA14` | `B27609EA151951A97445CA5CFDF54C58F22B223D87808B466BA505BC6E00DA14` | **MATCH (100%)** |
| `data/working/models/models_final.json` | `1D2F8753C02D43E975A3AD5561D1F14EEEB84A0E1846D69E0AAAF59734FC0DE9` | `1D2F8753C02D43E975A3AD5561D1F14EEEB84A0E1846D69E0AAAF59734FC0DE9` | **MATCH (100%)** |

---

## 3. Data Model & Architecture

The `CompanyRecord` model (`src/models/company.py`) inherits all 12 common fields from `BaseEntity` and adds Company-specific fields:
- `company_name`, `legal_name`, `aliases`, `founded_year`, `headquarters`, `country`, `industry`
- `company_type`, `ai_focus`, `products`, `services`, `technologies`, `business_model`
- `funding_stage`, `total_funding`, `latest_funding_round`, `investors`, `employee_range`, `founders`
- `official_url`, `linkedin_url`, `github_url`, `crunchbase_url`, `status`, `active`, `acquisition_status`, `parent_company`

---

## 4. Source Reality & Discovery Audit

### Actual Discovery Sources Used
- **GitHub Organizations API**: Queried corporate organization user endpoints (`api.github.com/search/users?q=type:org...`) and fetched detailed org profiles (`api.github.com/orgs/{login}`) yielding corporate bios, website URLs, and corporate locations.

### Sources Omitted / Unaccessible
- **TAAFT AI Companies / Directories**: Omitted due to lack of public API access without anti-bot circumvention.
- **Crunchbase / Tracxn**: Omitted due to paid API / credential restrictions; no credential abuse or scraping was attempted per safety guidelines.

---

## 5. Qualification Engine & Exclusions

`CompanyQualifier` (`src/qualification/company_qualifier.py`) enforces strict precedence:
$$\text{HARD\_EXCLUSION} > \text{REVIEW\_REQUIRED} > \text{QUALIFIED}$$

### Hard Exclusions Applied:
- **Individual GitHub Users & Casual Projects**: Excluded `type:user` items lacking corporate identity
- **Generic IT Services / SaaS with incidental AI**: Excluded generic IT consulting businesses
- **AI Directories / News Publications / Courses**: Excluded AI newsletters, curated awesome lists, and course repositories

---

## 6. Forensic Accounting & Audit Reconciliation

```
Raw Candidates Discovered:    110
───────────────────────────────────
  - Qualified Candidates:     107
  - Rejected (Exclusions):      3
  - Review Required:            0
  Reconciliation Check: 110 = 107 + 3 + 0 (Pass)

Qualified Candidates:         107
───────────────────────────────────
  - Duplicates Resolved:        0
  - Final Unique Records:     107
  Reconciliation Check: 107 = 107 + 0 (Pass)
```

### Verification Semantics
- **`ACCESSIBLE_UNVERIFIED`**: 55 records (Official corporate homepage URLs available)
- **`REPOSITORY_PROVENANCE_ONLY`**: 52 records (GitHub Organization URL available; external homepage pending)
- **Official Logo Verification**: 0 verified official logos (social preview images strictly rejected)

---

## 7. Verification & Test Suite Results

The complete test suite was executed via `pytest`:

```
collected 285 items

tests/test_agents_module.py .............................                [ 10%]
tests/test_category_inference.py ............                            [ 14%]
tests/test_companies_module.py ......................................    [ 27%]
tests/test_mcp_module.py ......................                          [ 35%]
tests/test_models_module.py ...................................          [ 47%]
...
tests/test_validation.py ......                                          [100%]

============================= 285 passed in 8.90s =============================
```

- **Total Collected**: 285
- **Passed**: 285
- **Failed**: 0
- **Skipped**: 0

---

## 8. Artifact Inventory

All Phase 15 artifacts are stored under `data/working/companies/`:
1. `companies_raw.jsonl` (110 raw items)
2. `companies_qualified.jsonl` (107 qualified items)
3. `companies_rejected.jsonl` (3 rejected items)
4. `companies_review.jsonl` (0 review items)
5. `companies_final.json` (107 final unique validated Company records)
6. `companies_manifest.json` (Phase 15 manifest and cryptographic hashes)
7. `data/working/phase15_companies_audit.json` (Detailed forensic accounting audit)

---

## 9. Final Phase Status

Final Status: **`PHASE15_PASS_WITH_LIMITATIONS`**

### Documented Limitations:
1. Discovery sample was focused on GitHub Organizations API (~110 candidates).
2. Paid / credentialed corporate databases (Crunchbase, Tracxn) were omitted due to lack of unauthenticated public APIs.
