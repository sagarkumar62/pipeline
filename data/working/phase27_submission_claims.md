# Phase 27 — Submission Claims Boundary Matrix

## SAFE TO CLAIM (Defensible Facts)
1. **Unified Dataset Scale**: Consolidated **8,318 total records** across 10 worksheets into a single public Google Spreadsheet.
2. **Tools Dataset Size**: Exceeded 1,000-record trial target; **3,500 Tool records accepted by the expansion pipeline and included in the unified dataset** (50 golden baseline + 3,450 expansion records).
3. **Public Spreadsheet Integration**: Published all 10 module worksheets to Google Spreadsheet ID `1COdZaxjJcangOa56qZ7CbUHowUAEsKcnUchHPSM8DQo` with 100% API readback verification.
4. **News Ingestion & Clustering**: Ingested **418 qualified news articles** across 19 active RSS feeds and assigned **415 event clusters**.
5. **Baseline Immutability**: 100% of protected baseline and expansion artifacts remained byte-for-byte unchanged (`PROTECTED_ARTIFACTS_CHANGED = 0`).
6. **Provenance Completeness**: 100% of published records contain traceable discovery metadata and source URLs.
7. **Security Hygiene**: Zero credentials or API keys exposed in repository, exported CSVs, or documentation.
8. **Test Verification**: 386 unit tests passed cleanly across the entire pipeline.
9. **LLM Infrastructure**: LLM provider fallback chain (`Gemini Flash` -> `Groq Llama` -> `DeepSeek`) and grounding validator implemented and tested on sample runs.
10. **Entity Resolution Pipeline**: Implemented 4-stage entity resolution pipeline (normalization, candidate blocking, identity evidence/similarity comparison, deterministic decision).

---

## DO NOT CLAIM (Undefensible Overclaims)
1. **DO NOT CLAIM** 50,000 Tools or 10,000 Companies completed (Current unified total is 8,318 records).
2. **DO NOT CLAIM** all 3,500 Tools received golden-baseline-level manual validation or bulk LLM enrichment.
3. **DO NOT CLAIM** TAAFT, Creati.ai, Crunchbase, Tracxn, or Futurepedia were used (Omitted due to lack of public APIs without anti-bot circumvention).
4. **DO NOT CLAIM** the 100-point Tool scoring framework was applied to the expansion dataset.
5. **DO NOT CLAIM** the dataset contains the "best" or "highest-scoring" tools.
6. **DO NOT CLAIM** all records were bulk LLM-enriched (Source-grounded facts were preserved directly).
7. **DO NOT CLAIM** 100% of records have verified external official websites or verified official logos.
8. **DO NOT CLAIM** SHA-256 itself constitutes entity resolution (SHA-256 hashes & canonical URL hashes are stable identifiers and change-detection fingerprints).
9. **DO NOT CLAIM** Videos target was completed (Videos dataset currently contains 0 records).
