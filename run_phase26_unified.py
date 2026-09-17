import os
import json
import csv
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple

from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

from src.utils.logging import setup_logger

load_dotenv()
logger = setup_logger("run_phase26_unified")

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1COdZaxjJcangOa56qZ7CbUHowUAEsKcnUchHPSM8DQo")
CREDENTIALS_JSON_PATH = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "credentials/google-sheets-service-account.json")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

MODULE_AUTHORITATIVE_SOURCES = {
    "Tools": {
        "file": "data/working/tools_expansion/tools_merged_proposed.json",
        "worksheet": "Tools"
    },
    "Companies": {
        "file": "data/working/companies_expansion/companies_merged_proposed.json",
        "worksheet": "Companies"
    },
    "Agents": {
        "file": "data/working/agents_expansion/agents_merged_proposed.json",
        "worksheet": "Agents"
    },
    "MCP": {
        "file": "data/working/mcp_expansion/mcp_merged_proposed.json",
        "worksheet": "MCP"
    },
    "Models": {
        "file": "data/working/models_expansion/models_merged_proposed.json",
        "worksheet": "Models"
    },
    "Robots": {
        "file": "data/working/robots_expansion/robots_merged_proposed.json",
        "worksheet": "Robots"
    },
    "Devices": {
        "file": "data/working/devices_expansion/devices_merged_proposed.json",
        "worksheet": "Devices"
    },
    "Repositories": {
        "file": "data/working/repositories/repositories_final.json",
        "worksheet": "Repositories"
    },
    "Videos": {
        "file": None,
        "worksheet": "Videos"
    },
    "News": {
        "file": "data/working/news/final_news.json",
        "worksheet": "News"
    }
}

MODULE_CSV_HEADERS = {
    "Tools": [
        "Record ID", "Name", "Description", "Official Website", "Official Logo",
        "GitHub Repository", "Categories", "Source", "Source URL",
        "Website Verified", "Logo Verified", "Description Grounded"
    ],
    "Companies": [
        "Record ID", "Company Name", "Description", "Official Website", "Official Logo",
        "Headquarters", "Founding Year", "Categories", "Source", "Source URL",
        "Website Verified", "Logo Verified"
    ],
    "Agents": [
        "Record ID", "Agent Name", "Description", "Official Website", "Repository URL",
        "Framework / SDK", "Agent Type", "Capabilities", "Source", "Source URL",
        "Website Verified"
    ],
    "MCP": [
        "Record ID", "MCP Name", "Description", "Official Website", "Repository URL",
        "Transport", "Capabilities", "Categories", "Source", "Source URL",
        "Website Verified"
    ],
    "Models": [
        "Record ID", "Model Name", "Description", "Provider / Organization", "Model Family",
        "Parameter Size", "Modality", "License", "Source", "Source URL",
        "Website Verified"
    ],
    "Robots": [
        "Record ID", "Robot Name", "Description", "Manufacturer", "Robot Type",
        "Form Factor", "Commercial Status", "Official Website", "Source", "Source URL",
        "Website Verified"
    ],
    "Devices": [
        "Record ID", "Device Name", "Description", "Manufacturer", "Device Type",
        "Physical Form", "Processor / NPU", "Memory / Storage", "Official Website",
        "Source", "Source URL", "Website Verified"
    ],
    "Repositories": [
        "Record ID", "Repository Name", "Description", "Repository URL", "Primary Language",
        "Stars", "Forks", "License", "Source", "Source URL"
    ],
    "Videos": [
        "Record ID", "Video Title", "Description", "Platform / Source", "Video URL",
        "Channel Name", "Duration Seconds", "Published At", "Source URL"
    ],
    "News": [
        "Record ID", "Article Title", "Summary", "Source Name", "Source Domain",
        "Canonical URL", "Published At", "Author", "Categories", "Event Cluster ID",
        "Source URL"
    ]
}


def compute_file_sha256(filepath: str) -> str:
    """Computes SHA-256 hash of a file."""
    if not filepath or not os.path.exists(filepath):
        return "FILE_NOT_FOUND"
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def format_record_for_csv(module: str, item: Dict[str, Any]) -> Dict[str, str]:
    """Transforms raw record dictionary to formatted row dict matching MODULE_CSV_HEADERS."""
    cats = item.get("categories", [])
    cats_str = " | ".join(cats) if isinstance(cats, list) else str(cats or "")

    disc = item.get("discovery_source") or item.get("source") or {}
    source_name = disc.get("name", "GitHub API") if isinstance(disc, dict) else str(disc)
    source_url = disc.get("url", "") if isinstance(disc, dict) else ""

    rec_id = item.get("id", "")
    name = item.get("name") or item.get("title") or ""
    desc = item.get("description") or item.get("summary") or ""
    official_url = item.get("official_url") or item.get("url") or item.get("canonical_url") or ""
    logo_url = item.get("logo_url") or item.get("logo") or ""
    repo_url = item.get("repository_url") or item.get("github_repo_url") or ""

    web_ver = "True" if item.get("website_verified", False) else "False"
    logo_ver = "True" if item.get("logo_verified", False) else "False"
    desc_gr = "True" if item.get("description_grounded", False) else "False"

    if module == "Tools":
        return {
            "Record ID": rec_id,
            "Name": name,
            "Description": desc,
            "Official Website": official_url if official_url.startswith("http") else "",
            "Official Logo": logo_url,
            "GitHub Repository": repo_url,
            "Categories": cats_str,
            "Source": source_name,
            "Source URL": source_url or repo_url or official_url,
            "Website Verified": web_ver,
            "Logo Verified": logo_ver,
            "Description Grounded": desc_gr
        }
    elif module == "Companies":
        return {
            "Record ID": rec_id,
            "Company Name": name,
            "Description": desc,
            "Official Website": official_url,
            "Official Logo": logo_url,
            "Headquarters": item.get("headquarters") or "",
            "Founding Year": str(item.get("founding_year") or ""),
            "Categories": cats_str,
            "Source": source_name,
            "Source URL": source_url or official_url,
            "Website Verified": web_ver,
            "Logo Verified": logo_ver
        }
    elif module == "Agents":
        return {
            "Record ID": rec_id,
            "Agent Name": name,
            "Description": desc,
            "Official Website": official_url,
            "Repository URL": repo_url,
            "Framework / SDK": item.get("framework_sdk") or "",
            "Agent Type": item.get("agent_type") or "",
            "Capabilities": " | ".join(item.get("capabilities", [])) if isinstance(item.get("capabilities"), list) else str(item.get("capabilities") or ""),
            "Source": source_name,
            "Source URL": source_url or repo_url or official_url,
            "Website Verified": web_ver
        }
    elif module == "MCP":
        return {
            "Record ID": rec_id,
            "MCP Name": name,
            "Description": desc,
            "Official Website": official_url,
            "Repository URL": repo_url,
            "Transport": " | ".join(item.get("transport", [])) if isinstance(item.get("transport"), list) else str(item.get("transport") or ""),
            "Capabilities": " | ".join(item.get("capabilities", [])) if isinstance(item.get("capabilities"), list) else str(item.get("capabilities") or ""),
            "Categories": cats_str,
            "Source": source_name,
            "Source URL": source_url or repo_url,
            "Website Verified": web_ver
        }
    elif module == "Models":
        return {
            "Record ID": rec_id,
            "Model Name": name,
            "Description": desc,
            "Provider / Organization": item.get("provider") or item.get("organization") or "",
            "Model Family": item.get("model_family") or "",
            "Parameter Size": str(item.get("parameter_size") or ""),
            "Modality": " | ".join(item.get("modality", [])) if isinstance(item.get("modality"), list) else str(item.get("modality") or ""),
            "License": item.get("license") or "",
            "Source": source_name,
            "Source URL": source_url or official_url,
            "Website Verified": web_ver
        }
    elif module == "Robots":
        return {
            "Record ID": rec_id,
            "Robot Name": name,
            "Description": desc,
            "Manufacturer": item.get("manufacturer") or "",
            "Robot Type": item.get("robot_type") or "",
            "Form Factor": item.get("form_factor") or "",
            "Commercial Status": item.get("commercial_status") or "",
            "Official Website": official_url,
            "Source": source_name,
            "Source URL": source_url or official_url,
            "Website Verified": web_ver
        }
    elif module == "Devices":
        return {
            "Record ID": rec_id,
            "Device Name": name,
            "Description": desc,
            "Manufacturer": item.get("manufacturer") or "",
            "Device Type": item.get("device_type") or "",
            "Physical Form": item.get("physical_form") or "",
            "Processor / NPU": item.get("processor") or "",
            "Memory / Storage": item.get("memory_storage") or item.get("memory") or "",
            "Official Website": official_url,
            "Source": source_name,
            "Source URL": source_url or official_url,
            "Website Verified": web_ver
        }
    elif module == "Repositories":
        return {
            "Record ID": rec_id,
            "Repository Name": name,
            "Description": desc,
            "Repository URL": official_url or repo_url,
            "Primary Language": item.get("language") or item.get("primary_language") or "",
            "Stars": str(item.get("stars") or item.get("stargazers_count") or 0),
            "Forks": str(item.get("forks") or item.get("forks_count") or 0),
            "License": item.get("license") or "",
            "Source": source_name,
            "Source URL": source_url or official_url
        }
    elif module == "Videos":
        return {
            "Record ID": rec_id,
            "Video Title": name,
            "Description": desc,
            "Platform / Source": item.get("platform") or "YouTube",
            "Video URL": official_url,
            "Channel Name": item.get("channel_name") or "",
            "Duration Seconds": str(item.get("duration_seconds") or ""),
            "Published At": item.get("published_at") or "",
            "Source URL": source_url or official_url
        }
    elif module == "News":
        return {
            "Record ID": rec_id,
            "Article Title": item.get("title") or name,
            "Summary": desc,
            "Source Name": item.get("source_name") or "",
            "Source Domain": item.get("source_domain") or "",
            "Canonical URL": item.get("canonical_url") or official_url,
            "Published At": item.get("published_at") or "",
            "Author": item.get("author") or "",
            "Categories": cats_str,
            "Event Cluster ID": item.get("event_cluster_id") or "",
            "Source URL": item.get("source_url") or source_url or official_url
        }
    return {}


def main():
    logger.info("=== STARTING PHASE 26: UNIFIED MULTI-MODULE DATASET CONSOLIDATION ===")

    # 1. Setup Directories & Compute Pre-execution Hashes
    export_dir = "data/working/phase26_sheet_exports"
    os.makedirs(export_dir, exist_ok=True)

    input_file_paths = [v["file"] for v in MODULE_AUTHORITATIVE_SOURCES.values() if v["file"] is not None]
    logger.info("Computing pre-consolidation SHA-256 hashes for authoritative module input artifacts...")
    pre_hashes = {p: compute_file_sha256(p) for p in input_file_paths}

    # 2. Load Datasets & Perform Local & Cross-Module Analysis
    module_records: Dict[str, List[Dict[str, Any]]] = {}
    total_record_count = 0
    id_map: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}

    for module, info in MODULE_AUTHORITATIVE_SOURCES.items():
        fpath = info["file"]
        if fpath and os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                records = json.load(f)
            module_records[module] = records
            total_record_count += len(records)
            logger.info(f"Loaded {len(records)} authoritative records for module '{module}'")

            for r in records:
                rid = r.get("id")
                if rid:
                    if rid not in id_map:
                        id_map[rid] = []
                    id_map[rid].append((module, r))
        else:
            module_records[module] = []
            logger.info(f"Loaded 0 records for module '{module}' (Path: {fpath})")

    # 3. Cross-Module Collisions Audit
    collisions: List[Dict[str, Any]] = []
    for rid, occurrences in id_map.items():
        if len(occurrences) > 1:
            modules_involved = list(set(o[0] for o in occurrences))
            if len(modules_involved) > 1:
                # Cross-module collision
                c_type = "CROSS_MODULE_ID_COLLISION"
                decision = "LEGITIMATE_CROSS_MODULE_RELATIONSHIP" if len(set(o[1].get("entity_type") for o in occurrences)) > 1 else "TRUE_DUPLICATE"
                collisions.append({
                    "id": rid,
                    "modules": modules_involved,
                    "collision_type": c_type,
                    "decision": decision,
                    "occurrences": len(occurrences)
                })

    collisions_path = "data/working/phase26_cross_module_collisions.jsonl"
    with open(collisions_path, "w", encoding="utf-8") as f:
        for c in collisions:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    logger.info(f"Cross-module collision audit complete: {len(collisions)} collisions recorded.")

    # 4. Export Publication-Ready CSV Files
    export_summary: Dict[str, Dict[str, Any]] = {}
    for module, records in module_records.items():
        headers = MODULE_CSV_HEADERS[module]
        csv_filename = f"{module.lower()}.csv"
        csv_path = os.path.join(export_dir, csv_filename)

        formatted_rows = [format_record_for_csv(module, r) for r in records]

        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            for row in formatted_rows:
                writer.writerow(row)

        export_summary[module] = {
            "csv_path": csv_path,
            "authoritative_count": len(records),
            "export_rows": len(formatted_rows),
            "headers": headers,
            "file_sha256": compute_file_sha256(csv_path)
        }
        logger.info(f"Generated publication CSV for '{module}': {len(formatted_rows)} rows -> {csv_path}")

    # 5. Authenticate with Google Sheets API & Upload Worksheets
    logger.info(f"Authenticating with Google Sheets API for Spreadsheet ID: {GOOGLE_SHEET_ID}...")
    with open(CREDENTIALS_JSON_PATH, "r", encoding="utf-8") as f:
        cred_info = json.load(f)
    if "private_key" in cred_info and "\\n" in cred_info["private_key"]:
        cred_info["private_key"] = cred_info["private_key"].replace("\\n", "\n")

    creds = Credentials.from_service_account_info(cred_info, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)

    published_summary: Dict[str, Dict[str, Any]] = {}

    for module, info in export_summary.items():
        ws_name = MODULE_AUTHORITATIVE_SOURCES[module]["worksheet"]
        headers = info["headers"]
        records = module_records[module]
        formatted_rows = [format_record_for_csv(module, r) for r in records]

        try:
            worksheet = spreadsheet.worksheet(ws_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=ws_name, rows="100", cols="20")

        worksheet.clear()

        # Build raw cell matrix: Row 1 = Headers, Rows 2..N = Data
        def stringify_val(v):
            if v is None:
                return ""
            if isinstance(v, list):
                return " | ".join(str(x) for x in v)
            if isinstance(v, dict):
                return json.dumps(v, ensure_ascii=False)
            return str(v)

        grid_data = [headers]
        for frow in formatted_rows:
            grid_data.append([stringify_val(frow.get(h, "")) for h in headers])

        if len(grid_data) > 0:
            worksheet.update(values=grid_data, range_name="A1")

        logger.info(f"Uploaded {len(formatted_rows)} data rows to Google Sheet worksheet '{ws_name}'")

        # Read back verification
        readback_values = worksheet.get_all_values()
        readback_headers = readback_values[0] if readback_values else []
        readback_data_rows = len(readback_values) - 1 if len(readback_values) > 0 else 0

        header_match = (readback_headers == headers)
        row_count_match = (readback_data_rows == len(formatted_rows))

        published_summary[module] = {
            "worksheet_name": ws_name,
            "write_success": True,
            "readback_success": True,
            "published_rows": readback_data_rows,
            "row_count_match": row_count_match,
            "header_match": header_match
        }

        logger.info(f"Readback verification for '{ws_name}': Data Rows={readback_data_rows}, Header Match={header_match}, Row Count Match={row_count_match}")

        if not (header_match and row_count_match):
            raise RuntimeError(f"Readback verification failed for worksheet '{ws_name}'!")

    # 6. Post-consolidation SHA-256 Safety Verification
    post_hashes = {p: compute_file_sha256(p) for p in input_file_paths}
    changed_files = [p for p in input_file_paths if pre_hashes[p] != post_hashes[p]]

    if changed_files:
        logger.error(f"CRITICAL SAFETY VIOLATION: {len(changed_files)} authoritative module artifacts were modified!")
        for fpath in changed_files:
            logger.error(f"  Modified: {fpath}")
        raise RuntimeError("Authoritative module baseline integrity violated. Pipeline halted.")
    else:
        logger.info("Post-consolidation safety check verified: 100% of authoritative module artifacts remain byte-for-byte identical!")

    # 7. Generate Manifest & Audit JSON Reports
    manifest_data = {
        "phase": "PHASE_26",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "google_sheet_id": GOOGLE_SHEET_ID,
        "google_sheet_url": f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/edit",
        "total_unified_records": total_record_count,
        "module_summary": {
            m: {
                "authoritative_count": export_summary[m]["authoritative_count"],
                "export_rows": export_summary[m]["export_rows"],
                "published_rows": published_summary[m]["published_rows"],
                "readback_success": published_summary[m]["readback_success"]
            } for m in MODULE_AUTHORITATIVE_SOURCES
        },
        "protected_artifact_sha256": post_hashes,
        "protected_artifacts_changed_count": len(changed_files)
    }

    manifest_path = "data/working/phase26_unified_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    audit_data = {
        "phase": "PHASE_26",
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "google_sheet_id": GOOGLE_SHEET_ID,
        "google_sheet_url": f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/edit",
        "total_unified_records": total_record_count,
        "module_table": [
            {
                "module": m,
                "authoritative_records": export_summary[m]["authoritative_count"],
                "export_rows": export_summary[m]["export_rows"],
                "published_rows": published_summary[m]["published_rows"]
            } for m in MODULE_AUTHORITATIVE_SOURCES
        ],
        "cross_module_collisions_count": len(collisions),
        "readback_verification_passed": all(p["readback_success"] and p["row_count_match"] and p["header_match"] for p in published_summary.values()),
        "protected_artifacts_changed_count": len(changed_files),
        "status": "PHASE26_PASS" if (len(changed_files) == 0 and all(p["readback_success"] for p in published_summary.values())) else "PHASE26_BLOCKED"
    }

    audit_path = "data/working/phase26_unified_audit.json"
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    logger.info(f"=== PHASE 26 CONSOLIDATION & PUBLIC PUBLICATION COMPLETE. Total Unified Records Published: {total_record_count} across 10 Worksheets. ===")


if __name__ == "__main__":
    main()
