import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from src.utils.logging import setup_logger

logger = setup_logger("baseline_manager")

TOOLS_JSON_PATH = Path("data/exports/tools.json")
MANIFEST_PATH = Path("data/working/baseline_manifest.json")


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class BaselineManifestManager:
    """
    Manages the 50-record golden baseline reference, manifest generation,
    sha256 checksum verification, and baseline record anchoring for expansion safety.
    """

    def __init__(self, tools_path: Path = TOOLS_JSON_PATH, manifest_path: Path = MANIFEST_PATH):
        self.tools_path = Path(tools_path)
        self.manifest_path = Path(manifest_path)
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

    def load_baseline_records(self) -> List[Dict[str, Any]]:
        """Loads and returns the frozen 50 canonical records from tools.json."""
        if not self.tools_path.exists():
            raise FileNotFoundError(f"Canonical baseline dataset not found at {self.tools_path}")
        
        with open(self.tools_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        if len(records) != 50:
            raise ValueError(f"Expected exactly 50 records in baseline dataset, got {len(records)}")

        return records

    def create_manifest(self) -> Dict[str, Any]:
        """
        Creates an immutable baseline integrity manifest containing
        file-level sha256 checksum, record count, and per-record field signatures.
        """
        if not self.tools_path.exists():
            raise FileNotFoundError(f"Canonical dataset not found at {self.tools_path}")

        raw_bytes = self.tools_path.read_bytes()
        file_sha256 = compute_sha256(raw_bytes)
        records = json.loads(raw_bytes.decode("utf-8"))

        record_entries = []
        for r in records:
            rec_id = r.get("id")
            name = r.get("name")
            official_url = r.get("official_url") or ""
            github_url = r.get("github_repo_url") or ""
            desc = r.get("description") or ""

            # Signature hash for per-record immutability check
            sig_raw = f"{rec_id}|{name}|{official_url}|{github_url}|{desc}".encode("utf-8")
            sig_hash = compute_sha256(sig_raw)

            record_entries.append({
                "id": rec_id,
                "name": name,
                "official_url": official_url,
                "github_repo_url": github_url,
                "signature": sig_hash
            })

        manifest = {
            "baseline_file": str(self.tools_path),
            "record_count": len(records),
            "file_sha256": file_sha256,
            "file_size_bytes": len(raw_bytes),
            "created_at": "2026-09-17T09:55:00Z",
            "records": record_entries
        }

        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Created baseline manifest with {len(records)} records at {self.manifest_path}")
        return manifest

    def verify_baseline(self) -> Dict[str, Any]:
        """
        Verifies that data/exports/tools.json matches the baseline manifest byte-for-byte and record-for-record.
        """
        if not self.manifest_path.exists():
            self.create_manifest()

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        if not self.tools_path.exists():
            return {"status": "FAIL", "reason": f"Tools file missing: {self.tools_path}"}

        raw_bytes = self.tools_path.read_bytes()
        current_sha256 = compute_sha256(raw_bytes)

        if current_sha256 != manifest["file_sha256"]:
            return {
                "status": "FAIL",
                "reason": f"File SHA256 mismatch: {current_sha256} != {manifest['file_sha256']}"
            }

        records = json.loads(raw_bytes.decode("utf-8"))
        if len(records) != manifest["record_count"]:
            return {
                "status": "FAIL",
                "reason": f"Record count mismatch: {len(records)} != {manifest['record_count']}"
            }

        return {
            "status": "PASS",
            "record_count": len(records),
            "sha256": current_sha256,
            "manifest_file": str(self.manifest_path)
        }
