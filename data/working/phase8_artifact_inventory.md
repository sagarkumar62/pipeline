# Phase 8 — Authoritative Artifact Inventory
**AI ORBIT DATA INGESTION PIPELINE**

---

### Executive Overview
This document cataloging the authoritative artifacts of the AI Orbit Data Ingestion Pipeline demarcates immutable baseline exports, authoritative prepublication dataset files, diagnostic manifests, and configuration files.

---

### Artifact Catalog

| Artifact Path | Purpose | Authoritative | Frozen | Generated | Safe to Modify | Relationship to Final Dataset |
|---|---|---|---|---|---|---|
| `data/exports/tools.json` | Golden Baseline (50 records) | Yes | **YES** | No | **NO** | Immutable baseline anchor (`SHA256: 4520014c...`) |
| `data/exports/tools.csv` | Initial CSV export | No | Yes | Yes | No | Legacy 50-record export |
| `data/exports/tools.jsonl` | Initial JSONL export | No | Yes | Yes | No | Legacy 50-record export |
| `data/working/tools_phase6c_enriched.json` | Phase 6C Enriched Dataset | Yes | Yes | Yes | No | Primary enriched source dataset (1,304 records) |
| `data/working/tools_final_1304_prepublication.csv` | Final Prepublication CSV | **YES** | **YES** | Yes | **NO** | Authoritative CSV published to Google Sheets (`SHA256: 75053362...`) |
| `data/working/tools_final_1304_prepublication.json` | Final Prepublication JSON | **YES** | **YES** | Yes | **NO** | Authoritative JSON published to Google Sheets (`SHA256: 58240472...`) |
| `data/working/phase6d_correction_manifest.json` | Machine Remediation Manifest | Yes | Yes | Yes | No | Records `anansi` description remediation |
| `data/working/phase6d_correction_report.md` | Phase 6D Audit Report | Yes | Yes | Yes | No | Documents Phase 6D quality & publication audit |
| `data/working/phase7_final_submission_audit.md` | Phase 7 Submission Audit Report | Yes | Yes | Yes | No | Final submission audit report |
| `data/working/phase7a_submission_hygiene_report.md` | Phase 7A Hygiene Report | Yes | Yes | Yes | No | Documents credential protection & git hygiene |
| `data/working/phase8_project_documentation_audit.md` | Phase 8 Documentation Audit | Yes | Yes | Yes | No | Phase 8 evaluation readiness audit report |
| `data/working/phase8_artifact_inventory.md` | Phase 8 Artifact Inventory | Yes | Yes | Yes | No | This document |
| `data/working/phase8_evaluation_readiness_checklist.md` | Evaluation Readiness Checklist | Yes | Yes | Yes | No | Evaluator readiness verification checklist |
| `README.md` | Evaluator Documentation Package | **YES** | No | No | Yes | Primary evaluator documentation file |
| `configs/settings.yaml` | Taxonomy & Config Settings | Yes | Yes | No | No | Defines taxonomy categories and thresholds |
| `.gitignore` | Git Protection Rules | Yes | No | No | Yes | Protects `credentials/` and `.env` files |
| `credentials/google-sheets-service-account.json` | Service Account Key | Private | Yes | No | **NO** | Google Sheets API publishing credentials (ignored) |

---

### Integrity Summary
- **Golden Baseline SHA256**: `4520014c9a1676f9090be806087a92ac0e12fef3d3136a95860cff48388ff2a1`
- **Prepublication CSV SHA256**: `75053362d1c9cb05ce19bc9ea94574681df04005043fbfe10792099a134a02fb`
- **Prepublication JSON SHA256**: `58240472341523668813c140112ef69f1a61b2bfbef17380965c59807e6bad31`
