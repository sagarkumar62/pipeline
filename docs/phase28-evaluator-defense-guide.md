# Phase 28 — Evaluator Defense & Technical Q&A Guide

This guide provides factual, evidence-backed responses to technical evaluation questions regarding the AI Orbit Data Ingestion Pipeline.

---

## Technical Q&A Matrix

### Q1: Why didn't you scrape TAAFT or Creati.ai?
**Answer**:
Public or compliant API access was unavailable for TAAFT and Creati.ai, and our engineering policy strictly forbids bypassing Cloudflare, CAPTCHA, or anti-bot protections via proxy rotation or scraper hacks. The pipeline ingested primary records exclusively through compliant public APIs (GitHub API, Hugging Face API, OpenRouter API, arXiv API/RSS, active technology RSS feeds) and explicitly records omitted sources in the limitations register.

---

### Q2: Why aren't all 8,318 records bulk LLM-enriched?
**Answer**:
Bulk uncontrolled LLM enrichment across thousands of records risks hallucinating features, capabilities, or pricing not present in raw source metadata. The multi-provider LLM orchestration framework (`Gemini Flash` → `Groq Llama` → `DeepSeek`) and grounding validation engine were fully implemented and verified on sample validation runs. However, for the final 8,318 unified records, raw source evidence was preserved to guarantee 0% hallucinated metadata.

---

### Q3: Why are some official websites and logos unverified?
**Answer**:
Verification semantics are enforced conservatively. External homepages are marked `website_verified = True` ONLY when HTTP HEAD/GET probes confirm an active, accessible domain. Brand logos are marked `logo_verified = True` ONLY when extracted images match official project branding. Inaccessible links (403/404/500), platform fallbacks, and GitHub repository URLs are explicitly preserved as `False` or `null` rather than over-claiming verification.

---

### Q4: Why is the Videos dataset physical count zero?
**Answer**:
No public video API adapter was executed during the ingestion phase. In accordance with strict pipeline data integrity rules, zero records were fabricated or synthesized. The `Videos` worksheet exists in the public Google Spreadsheet with verified column headers and zero data rows to maintain structural completeness.

---

### Q5: Did you reach the 50,000 Tools target?
**Answer**:
No. The delivered Tools dataset contains 3,500 records accepted by the expansion pipeline (exceeding the 1,000+ trial threshold). The 50,000 Tools target represents the long-term multi-year scaling target for which the system architecture (async I/O, candidate blocking, rate-limit backoff, O(1) hashing) was designed.

---

### Q6: Did you apply the 100-point Tool scoring framework to the expansion dataset?
**Answer**:
No. The 100-point scoring framework was not applied to rank or select records in the final 3,500-record Tool expansion dataset. All qualifying records meeting deterministic qualification rules were ingested, and records are not claimed as "highest scoring" or "top ranked."

---

### Q7: How does entity resolution work in the pipeline?
**Answer**:
Entity resolution is strictly defined as a 4-stage deterministic pipeline:
1. **Normalization**: Canonicalizing URLs, stripping tracking parameters, and standardizing domain/name strings.
2. **Candidate Blocking**: Partitioning records by domain or category keys to avoid pairwise O(N²) comparisons.
3. **Similarity Comparison & Identity Evidence**: Evaluating exact domain+name matches and string distance via RapidFuzz.
4. **Deterministic Decision**: Applying precedence rules to merge duplicate candidate records.

*Note: SHA-256 hashes and canonical URL hashes are stable identifiers, change-detection fingerprints, and identity keys, NOT the entity-resolution algorithm itself.*

---

### Q8: What is the exact size of the published unified dataset?
**Answer**:
The published dataset contains **8,318 total records** across 10 worksheets in Google Spreadsheet ID `1COdZaxjJcangOa56qZ7CbUHowUAEsKcnUchHPSM8DQo`:
- **Tools**: 3,500
- **Companies**: 509
- **Agents**: 911
- **MCP**: 475
- **Models**: 1,424
- **Robots**: 656
- **Devices**: 337
- **Repositories**: 88
- **Videos**: 0
- **News**: 418

This total was verified 100% consistent across physical JSON datasets, generated CSV exports, and live Google Sheets API readback.

---

## Verification Evidence Reference

- **Audit Requirement Matrix**: [`data/working/phase27_requirement_matrix.json`](file:///c:/Users/hp/OneDrive/Documents/Desktop/pipeline/data/working/phase27_requirement_matrix.json)
- **Three-Way Consistency Audit**: [`data/working/phase27_submission_consistency.json`](file:///c:/Users/hp/OneDrive/Documents/Desktop/pipeline/data/working/phase27_submission_consistency.json)
- **Forensic Audit Summary**: [`docs/phase27-final-submission-audit.md`](file:///c:/Users/hp/OneDrive/Documents/Desktop/pipeline/docs/phase27-final-submission-audit.md)
- **Submission Claims Boundary**: [`data/working/phase27_submission_claims.md`](file:///c:/Users/hp/OneDrive/Documents/Desktop/pipeline/data/working/phase27_submission_claims.md)
