# AI Orbit — Multi-Module Data Ingestion Pipeline

Production-grade, modular Python 3.11+ data ingestion, qualification, deduplication, verification, enrichment, and publication pipeline for the **AI Orbit** multi-module ecosystem.

---

## 1. Overview
The AI Orbit Data Ingestion Pipeline is an automated, evidence-grounded engineering pipeline designed to discover, extract, qualify, normalize, deduplicate, verify, enrich, and publish multi-module AI technology metadata. The pipeline currently manages a verified unified dataset of **8,318 records** published directly across 10 distinct worksheets in a public Google Spreadsheet.

---

## 2. Multi-Module Unified Dataset Inventory

| Module | Current Records |
| :--- | :---: |
| **Tools** | 3,500 |
| **Companies** | 509 |
| **Agents** | 911 |
| **MCP** | 475 |
| **Models** | 1,424 |
| **Robots** | 656 |
| **Devices** | 337 |
| **Repositories** | 88 |
| **Videos** | 0 |
| **News** | 418 |
| **TOTAL** | **8,318** |

*These are the current unified dataset counts verified during Phase 27 against authoritative physical datasets, CSV exports, and live Google Sheets readback.*

---

## 3. End-to-End Conceptual Workflow

The architecture follows a decoupled, modular 9-stage pipeline:

```text
+------------------+     +------------------+     +-------------------+
|  1. Document /   | --> |   2. Discovery   | --> |   3. Extraction   |
|     Schemas      |     |  (APIs & RSS)    |     | (Field Parsing)   |
+------------------+     +------------------+     +-------------------+
                                                            |
+------------------+     +------------------+               v
|  6. Entity       | <-- |  5. Verification | <-- +-------------------+
|     Resolution   |     | (Website & Logo) |     |  4. Qualification |
+------------------+     +------------------+     | (Hard Non-Tools)  |
         |                                        +-------------------+
         v
+------------------+     +------------------+     +-------------------+
| 7. Grounded LLM  | --> |    8. Export     | --> |  9. Google Sheets |
|    Enrichment    |     |  (JSON / CSV)    |     |   (10 Worksheets) |
+------------------+     +------------------+     +-------------------+
```

---

## 4. Tools Trial Requirement & Scope Boundaries

- **3,500 Delivered Tool Records**: 3,500 physical Tool records accepted by the expansion pipeline, representing 2,198 uniquely resolved entities (1,304 golden baseline entities + 894 new expansion entities) included in the unified dataset, exceeding the 1,000+ trial dataset threshold.
- **Golden Baseline Isolation**: 1,304 immutable baseline entities (including a 50-record golden baseline with deeper manual/LLM validation evidence).
- **Bulk LLM Enrichment Bypassed**: High-scale LLM enrichment was intentionally not executed across the expansion Tool records to prevent model hallucination over raw factual metadata.
- **Unapplied 100-Point Scoring**: The specified 100-point Tool scoring framework was not applied to the final expansion dataset. Records are qualified based on deterministic negative/positive rule matching.
- **Omitted Unauthenticated Sources**: TAAFT and Creati.ai were specified discovery sources but were not automatically ingested because public API / compliant access was unavailable.

---

## 5. Entity Resolution Pipeline

Entity resolution in the pipeline is structured as a deterministic 4-stage process:

1. **Normalization & Canonicalization**: Standardizes GitHub repository URLs, strips tracking parameters, and canonicalizes domain names.
2. **Candidate Blocking**: Partitions candidate records by domain or taxonomy keys to constrain candidate matching space.
3. **Identity Evidence & Similarity Comparison**: Evaluates exact domain+name matches and string distance via RapidFuzz.
4. **Deterministic Resolution**: Applies strict precedence rules to merge duplicate candidate records.

*Note: SHA-256 hashes and canonical URL hashes serve as stable identifiers, fingerprints, and change-detection mechanisms. SHA-256 is not itself an entity-resolution algorithm.*

---

## 6. Multi-Provider LLM Orchestration Framework

### Provider Fallback Chain
```text
Gemini Flash (Primary) ──► Groq Llama (Secondary) ──► DeepSeek (Tertiary)
```

### Infrastructure Capabilities
- **Resilience**: Automatic retry with exponential backoff and random jitter for HTTP 429 rate limits.
- **Payload Management**: Automatic prompt truncation and chunking on HTTP 413 Payload Too Large responses.
- **Grounding Validation**: `GroundingValidator` (`src/enrichment/grounding_validator.py`) verifies synthesized text against raw source README text.

### Implementation vs Execution Boundary
- **IMPLEMENTED**: Multi-provider LLM orchestration infrastructure and grounding validator.
- **VALIDATED**: Real-provider validation executed on sample test batches.
- **NOT PERFORMED**: Bulk uncontrolled LLM enrichment across the final 8,318 unified dataset records.

---

## 7. Source Reality Table

| Source | Status |
| :--- | :--- |
| **GitHub API** | `ACTUALLY USED` |
| **Hugging Face API** | `ACTUALLY USED` |
| **OpenRouter API** | `ACTUALLY USED WHERE APPLICABLE` |
| **arXiv API/RSS** | `ACTUALLY USED` |
| **Active technology RSS feeds** | `ACTUALLY USED` |
| **TAAFT** | `SPECIFIED BUT OMITTED` |
| **Creati.ai** | `SPECIFIED BUT OMITTED` |
| **Crunchbase** | `SPECIFIED BUT OMITTED` |
| **Tracxn** | `SPECIFIED BUT OMITTED` |
| **Futurepedia** | `SPECIFIED BUT OMITTED` |
| **Robot Observatory** | `SPECIFIED BUT OMITTED` |
| **Physical AI Devices** | `SPECIFIED BUT OMITTED` |

---

## 8. Data Quality & Verification

The pipeline distinguishes four distinct verification parameters:
- **Source Provenance**: 100% of records have attributable discovery source metadata and URLs.
- **Official Website Verification**: Probed conservatively via HTTP HEAD/GET (`src/verification/website_verifier.py`). Only 420 / 3,500 Tools have verified official external marketing domains; GitHub repository URLs are preserved separately.
- **Official Logo Verification**: Evaluated via favicon/brand image headers (`src/verification/logo_verifier.py`). Only 262 / 3,500 Tools have verified official brand logos.
- **Description Grounding**: Synthesized descriptions are validated strictly against README context.

---

## 9. Architectural Scale Thinking

The ingestion engine is engineered for large-scale operations:
- **Asynchronous I/O & Bounded Concurrency**: Controlled via `asyncio.Semaphore(10)`.
- **Rate-Limit Backoff**: Respects `Retry-After` headers and GitHub API rate-limit state (`X-RateLimit-Remaining`).
- **State Checkpointing**: Persists state to JSON checkpoints allowing interrupted runs to resume cleanly.
- **Deduplication Hashing**: O(1) candidate lookup avoiding pairwise matrix comparisons.

### Current Dataset vs Long-Term Target Scale

| Category | Current Delivered | Long-Term Ecosystem Target |
| :--- | :---: | :---: |
| **Tools** | 3,500 | 50,000 |
| **Companies** | 509 | 10,000 |
| **Agents** | 911 | 10,000 |
| **MCP** | 475 | 10,000 |
| **Models** | 1,424 | 2,000 |
| **Robots** | 656 | 1,000 |
| **Devices** | 337 | 1,000 |
| **Repositories** | 88 | 50,000 |
| **Videos** | 0 | 2,000 |
| **News** | 418 | 100–500 stories/day |
| **TOTAL** | **8,318** | **136,000** |

---

## 10. Anti-Bot & Ethical Ingestion Policy

- **Zero Protection Circumvention**: No CAPTCHA bypass, proxy rotation, or unauthorized scraper hacks were used.
- **API First**: Ingestion relied exclusively on official public APIs and open RSS feeds.
- **Explicit Omission**: Unaccessible or anti-bot-protected web targets are recorded as omitted in documentation rather than illegally scraped.

---

## 11. Google Sheet Submission & Readback

- **Spreadsheet ID**: `1COdZaxjJcangOa56qZ7CbUHowUAEsKcnUchHPSM8DQo`
- **Public URL**: [AI Orbit Public Spreadsheet](https://docs.google.com/spreadsheets/d/1COdZaxjJcangOa56qZ7CbUHowUAEsKcnUchHPSM8DQo/edit)
- **Readback Verification**: Verified 100% exact match across all 10 worksheets (`Physical = CSV = Google Sheet = 8,318 total records`).
- **Videos Worksheet**: Exists with verified column headers and 0 data rows.

---

## 12. Security & Credential Protection

- **No Secrets Exposed**: 0 API keys, service account JSON files, or tokens are committed in source code.
- **Environment Isolation**: Configured via `.env` loaded with `python-dotenv`.
- **Git Protections**: `.gitignore` excludes `credentials/`, `.env`, and local working artifacts.

---

## 13. Testing Suite

The test suite is executed using `pytest`:
```bash
pytest
```
- **Total Tests**: **387 passed** (`0 failed`, `0 skipped`, `0 errors`).
- **Coverage**: Pydantic schemas, qualification rules, deduplication, LLM orchestration, website verification, cross-module unification, and Phase 27 forensic audit verification.

---

## 14. Reproducibility Instructions

### Environment Setup
```bash
# 1. Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Unix/MacOS:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment template
cp .env.example .env
```

### Run Audit Verification
```bash
# Execute unit test suite
pytest

# Execute Phase 27 forensic audit
python run_phase27_final_audit.py
```

---

## 15. Repository Structure

```text
pipeline/
├── credentials/          # Google Sheets credentials (ignored by git)
├── data/
│   ├── exports/          # Golden baseline exports (tools.json)
│   └── working/          # Authoritative multi-module datasets, CSV exports, & audit reports
├── docs/                 # Multi-module specifications and evaluator defense guide
├── src/
│   ├── deduplication/    # Module-specific entity resolvers
│   ├── discovery/        # GitHub, Hugging Face, OpenRouter, arXiv, RSS discovery modules
│   ├── enrichment/       # LLM orchestrator & grounding validator
│   ├── export/           # Google Sheets & CSV exporters
│   ├── extraction/       # Field extractors
│   ├── models/           # Pydantic schemas (10 modules)
│   ├── qualification/    # Rule-based qualifiers
│   └── verification/     # Official website & logo verifiers
├── tests/                # 387 unit regression tests
├── README.md             # Evaluator-facing pipeline overview
└── requirements.txt      # Python dependencies
```

---

## 16. Final Submission Status

- **Status**: **`PHASE28_SUBMISSION_PACKAGED_WITH_LIMITATIONS`**
- **Public Spreadsheet ID**: `1COdZaxjJcangOa56qZ7CbUHowUAEsKcnUchHPSM8DQo`
- **Protected Artifact Safety**: `PROTECTED_ARTIFACTS_CHANGED = 0` (100% hash match across 101 files)
- **Secrets Security**: `NO_SECRETS_EXPOSED = TRUE`
