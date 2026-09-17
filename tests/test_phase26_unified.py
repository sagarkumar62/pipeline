import os
import json
import csv
import pytest

from run_phase26_unified import MODULE_AUTHORITATIVE_SOURCES, MODULE_CSV_HEADERS, compute_file_sha256


def test_required_worksheet_names():
    expected_worksheets = [
        "Tools", "Companies", "Agents", "MCP", "Models",
        "Robots", "Devices", "Repositories", "Videos", "News"
    ]
    actual_worksheets = [info["worksheet"] for info in MODULE_AUTHORITATIVE_SOURCES.values()]
    assert actual_worksheets == expected_worksheets


def test_deterministic_csv_headers():
    for module, headers in MODULE_CSV_HEADERS.items():
        assert len(headers) >= 8
        assert "Record ID" in headers or "Name" in headers or "Article Title" in headers or "Video Title" in headers


def test_authoritative_artifacts_exist():
    for module, info in MODULE_AUTHORITATIVE_SOURCES.items():
        if info["file"] is not None:
            assert os.path.exists(info["file"]), f"Authoritative file for {module} missing: {info['file']}"


def test_export_csv_existence_and_row_counts():
    export_dir = "data/working/phase26_sheet_exports"
    if not os.path.exists(export_dir):
        pytest.skip("Export directory data/working/phase26_sheet_exports does not exist yet; run script first.")

    for module, info in MODULE_AUTHORITATIVE_SOURCES.items():
        csv_path = os.path.join(export_dir, f"{module.lower()}.csv")
        assert os.path.exists(csv_path), f"Export CSV for {module} missing: {csv_path}"

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

        header = rows[0]
        data_rows = rows[1:]

        assert header == MODULE_CSV_HEADERS[module]

        fpath = info["file"]
        if fpath and os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                records = json.load(f)
            assert len(data_rows) == len(records), f"Row count mismatch in {module}.csv: {len(data_rows)} vs {len(records)}"


def test_no_duplicate_ids_within_module_csv():
    export_dir = "data/working/phase26_sheet_exports"
    if not os.path.exists(export_dir):
        pytest.skip("Export directory data/working/phase26_sheet_exports does not exist yet; run script first.")

    for module in MODULE_AUTHORITATIVE_SOURCES:
        csv_path = os.path.join(export_dir, f"{module.lower()}.csv")
        if not os.path.exists(csv_path):
            continue

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            ids = [row.get("Record ID") for row in reader if row.get("Record ID")]

        assert len(ids) == len(set(ids)), f"Duplicate IDs found in {module}.csv!"


def test_no_secrets_in_csv_exports():
    export_dir = "data/working/phase26_sheet_exports"
    if not os.path.exists(export_dir):
        pytest.skip("Export directory data/working/phase26_sheet_exports does not exist yet; run script first.")

    forbidden = ["private_key", "service_account", "gsk_", "KEY01", "AQ.Ab8"]

    for module in MODULE_AUTHORITATIVE_SOURCES:
        csv_path = os.path.join(export_dir, f"{module.lower()}.csv")
        if not os.path.exists(csv_path):
            continue

        with open(csv_path, "r", encoding="utf-8") as f:
            content = f.read()

        for term in forbidden:
            assert term not in content, f"Forbidden secret string '{term}' detected in {module}.csv!"
