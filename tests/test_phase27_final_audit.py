import os
import json
import pytest


def test_phase27_audit_artifacts_exist():
    artifacts = [
        "data/working/phase27_requirement_matrix.json",
        "data/working/phase27_evidence_index.json",
        "data/working/phase27_limitations.json",
        "data/working/phase27_submission_consistency.json",
        "data/working/phase27_forensic_audit.json",
        "data/working/phase27_submission_claims.md",
        "docs/phase27-final-submission-audit.md"
    ]
    for path in artifacts:
        if not os.path.exists(path):
            pytest.skip(f"Artifact {path} not found; run python run_phase27_final_audit.py first.")
        assert os.path.exists(path)


def test_requirement_matrix_structure():
    matrix_path = "data/working/phase27_requirement_matrix.json"
    if not os.path.exists(matrix_path):
        pytest.skip("Requirement matrix not generated yet.")

    with open(matrix_path, "r", encoding="utf-8") as f:
        matrix = json.load(f)

    assert len(matrix) >= 25
    valid_statuses = {"PASS", "PARTIAL", "NOT_IMPLEMENTED", "NOT_VERIFIABLE"}

    req_ids = [r["id"] for r in matrix]
    assert "REQ_A" in req_ids
    assert "REQ_Q" in req_ids
    assert "REQ_Y" in req_ids

    for item in matrix:
        assert item["status"] in valid_statuses
        assert "evidence_file" in item
        assert "implementation_location" in item


def test_limitation_register_structure():
    lim_path = "data/working/phase27_limitations.json"
    if not os.path.exists(lim_path):
        pytest.skip("Limitations register not generated yet.")

    with open(lim_path, "r", encoding="utf-8") as f:
        limitations = json.load(f)

    assert len(limitations) >= 3
    for lim in limitations:
        assert "category" in lim
        assert "limitation" in lim
        assert "impact" in lim


def test_submission_consistency_counts():
    cons_path = "data/working/phase27_submission_consistency.json"
    if not os.path.exists(cons_path):
        pytest.skip("Consistency audit not generated yet.")

    with open(cons_path, "r", encoding="utf-8") as f:
        cons = json.load(f)

    assert cons["total_mismatches_count"] == 0
    assert cons["total_physical_authoritative_records"] == 8318
    assert cons["total_published_sheet_records"] == 8318


def test_forensic_audit_status():
    audit_path = "data/working/phase27_forensic_audit.json"
    if not os.path.exists(audit_path):
        pytest.skip("Forensic audit JSON not generated yet.")

    with open(audit_path, "r", encoding="utf-8") as f:
        audit = json.load(f)

    assert audit["status"] == "PHASE27_SUBMISSION_READY_WITH_LIMITATIONS"
    assert audit["inventory"]["total_published_records"] == 8318
    assert audit["google_spreadsheet"]["worksheets_count"] == 10
