import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Generator
from src.models.tool import ToolRecord


class CheckpointManager:
    """
    Manages structured ingestion checkpoints to support granular pipeline resume
    and idempotent execution across discovery source, query, page, and processing stage.
    """

    def __init__(self, checkpoint_file: str = "data/working/expansion_checkpoint.json"):
        self.checkpoint_file = Path(checkpoint_file)
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def get_checkpoint(self, source_name: str, query: Optional[str] = None) -> Optional[Dict[str, Any]]:
        key = f"{source_name}:{query}" if query else source_name
        return self._data.get(key)

    def update(
        self,
        source_name: str,
        query: Optional[str] = None,
        page: int = 1,
        stage: str = "DISCOVERY",
        last_id: Optional[str] = None,
        processed_count: int = 0,
        completed: bool = False
    ):
        key = f"{source_name}:{query}" if query else source_name
        self._data[key] = {
            "source_name": source_name,
            "query": query,
            "page": page,
            "stage": stage,
            "last_id": last_id,
            "processed_count": processed_count,
            "completed": completed,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        with open(self.checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def is_completed(self, source_name: str, query: Optional[str] = None, page: int = 1) -> bool:
        ckpt = self.get_checkpoint(source_name, query)
        if not ckpt:
            return False
        if ckpt.get("completed", False):
            return True
        return ckpt.get("page", 0) > page

    def clear(self):
        self._data = {}
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()


class StorageRepository:
    """
    Handles streaming raw JSONL persistence, validated outputs, working storage, and rejected records.
    """

    def __init__(self, base_dir: str = "data"):
        self.base_dir = Path(base_dir)
        self.working_dir = self.base_dir / "working"
        self.raw_dir = self.base_dir / "raw"
        self.cleaned_dir = self.base_dir / "cleaned"
        self.normalized_dir = self.base_dir / "normalized"
        self.validated_dir = self.base_dir / "validated"
        self.rejected_dir = self.base_dir / "rejected"
        self.exports_dir = self.base_dir / "exports"

        for directory in [
            self.working_dir, self.raw_dir, self.cleaned_dir, self.normalized_dir,
            self.validated_dir, self.rejected_dir, self.exports_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def save_raw_record(self, record: Dict[str, Any], source_name: str) -> str:
        """Appends a raw record to JSONL preserving source provenance."""
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        filepath = self.raw_dir / f"tools_{source_name.lower().replace(' ', '_')}_{date_str}.jsonl"

        payload = {
            "raw": record,
            "discovered_at": datetime.now(timezone.utc).isoformat(),
            "source_name": source_name
        }

        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

        return str(filepath)

    def stream_raw_records(self, filepath: str) -> Generator[Dict[str, Any], None, None]:
        """Streams raw records line-by-line to avoid memory overhead."""
        if not os.path.exists(filepath):
            return

        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    def save_validated(self, records: List[ToolRecord]):
        """Saves accepted canonical Tool records to JSONL."""
        filepath = self.validated_dir / "tools.jsonl"
        with open(filepath, "w", encoding="utf-8") as f:
            for record in records:
                f.write(record.model_dump_json(exclude_none=False) + "\n")

    def save_rejected(self, raw_record: Dict[str, Any], reason: str, stage: str):
        """Appends a rejected record with cause to the rejected log."""
        filepath = self.rejected_dir / "tools.jsonl"
        payload = {
            "record": raw_record,
            "reason": reason,
            "pipeline_stage": stage,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def clear_rejected(self):
        """Clears previous rejected records for a clean run."""
        filepath = self.rejected_dir / "tools.jsonl"
        if filepath.exists():
            filepath.unlink()
