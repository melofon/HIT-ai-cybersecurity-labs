from __future__ import annotations

import json
from pathlib import Path

from morpheus_lite.config import load_settings
from morpheus_lite.storage import AuditStore


def main() -> None:
    settings = load_settings()
    storage = settings.raw.get("storage", {})
    source = Path(storage.get("audit_jsonl", "data/audit.jsonl"))
    if not source.exists():
        raise SystemExit(f"No audit file found at {source}")
    records = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    store = AuditStore(source, storage.get("parquet_directory", "exports"))
    output = store.export_parquet(records)
    print(f"Exported {len(records)} records to {output}")


if __name__ == "__main__":
    main()
