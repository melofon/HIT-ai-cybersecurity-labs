from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


class AuditStore:
    def __init__(self, jsonl_path: str | Path, parquet_directory: str | Path) -> None:
        self.jsonl_path = Path(jsonl_path)
        self.parquet_directory = Path(parquet_directory)

    def append(self, record: dict[str, Any]) -> None:
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with self.jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, default=str) + "\n")

    def export_parquet(self, records: list[dict[str, Any]]) -> Path:
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError as exc:
            raise RuntimeError("Install pyarrow to export Parquet files") from exc
        self.parquet_directory.mkdir(parents=True, exist_ok=True)
        path = self.parquet_directory / f"morpheus_lite_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.parquet"
        normalized = [json.loads(json.dumps(item, default=str)) for item in records]
        pq.write_table(pa.Table.from_pylist(normalized), path)
        return path
