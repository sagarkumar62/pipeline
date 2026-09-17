# AI Orbit — Final Submission Manifest

**Submission Date**: September 17, 2026  
**Final Status**: `PHASE6_FINAL_DATASET_READY_FOR_GOOGLE_SHEET`  
**Test Suite**: **108 / 108 passed** ([`pytest -q`](file:///c:/Users/hp/OneDrive/Documents/Desktop/pipeline/tests/test_phase4d_remediation.py))  

---

## 1. Dataset Overview

- **Module**: `Tools`
- **Canonical Records**: `50`
- **Unique Record IDs**: `50`
- **Duplicate Records**: `0`
- **Export Format Consistency**: `100% Match` (`tools.json`, `tools.jsonl`, `tools.csv`, `ai_orbit_tools_final_google_sheet.csv`)

---

## 2. Dataset Quality Metrics

- **Description Grounding Rate**: **50 / 50 (100%)**
- **Tool Qualification Rate**: **50 / 50 (100%)**
- **Official External Websites**: **36 / 50 (72%)** (14 open-source repositories without separate websites retain `official_url = null`)
- **Verified Official Logos**: **35 / 50 (70%)**
- **Blocking Quality Issues**: **0**
- **Non-Blocking Review Items**: **6**

---

## 3. Pipeline Architecture

1. **Discovery**: External discovery via GitHub Search API targeting AI tools, agents, MCPs, and developer frameworks.
2. **Extraction**: Raw metadata, topics, website URLs, and README excerpts.
3. **Cleaning**: HTML tag stripping, boilerplate removal, non-breaking hyphen normalization.
4. **Normalization**: Canonical domain parsing, category mapping against 14 AI Orbit taxonomy categories.
5. **Deduplication**: Deterministic SHA-256 ID hash (`tool_<hash>`).
6. **Classification**: Taxonomy classification into primary & secondary categories.
7. **Verification**: HTTP GET verification of official websites and brand logo assets.
8. **LLM Enrichment**: Multi-provider fallback (`Gemini Flash` → `Groq Llama-3` → `DeepSeek`) with context budgeting and strict grounding validation.
9. **Validation Gate**: Automated schema enforcement via Pydantic `ToolRecord`.
10. **Export**: Multi-format exports (`tools.json`, `tools.jsonl`, `tools.csv`, `ai_orbit_tools_final_google_sheet.csv`).

---

## 4. Source Traceability

Every record in the canonical dataset is fully traceable to authentic source evidence:
- **Discovery Source**: `GitHub API Search` with legitimate repo endpoints.
- **Evidence Sources**: `GITHUB_REPOSITORY`, `OFFICIAL_WEBSITE`, `GITHUB_README`.
- **Zero Fabrication**: Descriptions are 100% grounded in extracted evidence packages without outside knowledge or ungrounded claims.

---

## 5. Google Sheet Publication Status

**Status**: `NOT PUBLISHED — CSV READY FOR MANUAL GOOGLE SHEETS IMPORT`

*Note*: Direct Google Sheets API publishing credentials were not configured in the workspace environment. Therefore, the pipeline generated an import-ready, perfectly formatted publication file at:
`data/exports/ai_orbit_tools_final_google_sheet.csv`

### Sheet Column Layout (Import-Ready):
1. `Name`
2. `Description`
3. `Official Website` (blank when `official_url` is null; never substituted with GitHub URL)
4. `Official Logo`
5. `GitHub Repository`
6. `Categories`
7. `Source`
8. `Source URL`
9. `Record ID`
10. `Website Verified`
11. `Logo Verified`
12. `Description Grounded`

---

## 6. Repository Package Structure

The submission repository includes all required directories and code modules:
- `src/`: Complete pipeline source code
- `data/exports/`: Frozen canonical datasets & Google Sheet CSV
- `tests/`: 108 unit regression tests
- `configs/`: Taxonomy & validation configs
- `docs/`: Audit documents and manifests
  - `phase4c_final_forensic_audit.md`
  - `phase4d_description_remediation.md`
  - `phase5_final_dataset_audit.md`
  - `phase5a_reconciliation.md`
  - `phase5a_reconciliation.json`
  - `final_submission_manifest.md`
- `run.py`: Pipeline entrypoint script
- `README.md`: System documentation
- `requirements.txt`: Python dependencies
- `.env.example`: Environment configuration template
