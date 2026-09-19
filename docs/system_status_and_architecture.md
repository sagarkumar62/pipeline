# AI Orbit — System Status & Architecture

## Current Project State
AI Orbit Data Ingestion Pipeline currently contains the historical 1,304-record Tools dataset.

- **Git Baseline Commit**: `cea5b20b6502401a1b0e508d7c7dcf52f4f2a602` (*Initial commit: AI Orbit Data Ingestion Pipeline*)
- **Scope**: Tools-only data ingestion pipeline checkpoint.
- **Other Modules**: Companies, Agents, MCP, Models, Robots, Devices, Repositories, Videos, and News are not created/populated in this checkpoint.

## Dataset Status & Integrity

| Metric / Parameter | Value | Verification Status |
| :--- | :--- | :--- |
| **Total Tools Records** | 1,304 | Verified |
| **Blank Record IDs** | 0 | Verified |
| **Blank Names** | 0 | Verified |
| **Blank URLs** | 0 | Verified |
| **Duplicate Record IDs** | 0 | Verified |
| **Duplicate Names** | 0 | Verified |
| **JSON SHA-256 Hash** | `58240472341523668813c140112ef69f1a61b2bfbef17380965c59807e6bad31` | Verified |
| **CSV SHA-256 Hash** | `75053362d1c9cb05ce19bc9ea94574681df04005043fbfe10792099a134a02fb` | Verified |
| **Google Sheet Worksheet** | `Tools` (1,304 data rows) | Verified |

## Architecture & Verification Terminology

- **SHA-256 Hashing**: Provides deterministic fingerprints / content hashes for record tracking and file integrity validation.
- **HTTP Response Codes**: Serves as accessibility evidence for external URLs (e.g., verifying web page reachability).
- **Official Identity Verification**: Evaluated separately from simple URL accessibility.
- **Data Provenance**: Explicitly tracks source lineage (e.g., GitHub API, official AI directory seed).
