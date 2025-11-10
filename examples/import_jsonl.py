from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.workproof.config import default_config
from src.workproof.database import initialize, insert_log, LogRecord


def import_jsonl(path: Path) -> None:
    cfg = default_config()
    initialize(cfg.db_path)
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            ts = datetime.fromisoformat(obj["timestamp"])
            rec = LogRecord(
                timestamp=ts,
                active_app=obj.get("active_app"),
                running_apps=json.dumps(obj.get("running_apps") or []),
                idle_seconds=int(obj.get("idle_seconds") or 0),
                project_path=obj.get("project_path"),
                event_type=obj.get("event_type"),
                meta=json.dumps(obj.get("meta")) if obj.get("meta") is not None else None,
            )
            insert_log(cfg.db_path, rec)
    print("Imported logs:", path)


if __name__ == "__main__":
    import_jsonl(Path("dev_data/sample_logs.jsonl"))


