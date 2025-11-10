from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.workproof.database import initialize, insert_log, LogRecord
from src.workproof.config import default_config


def main() -> None:
    cfg = default_config()
    initialize(cfg.db_path)
    base = datetime.now(timezone.utc).replace(hour=10, minute=0, second=0, microsecond=0)
    for i in range(20):
        insert_log(cfg.db_path, LogRecord(base + timedelta(minutes=i), "VSCode", "[]", 5, None, "sample", None))
    for i in range(10):
        insert_log(cfg.db_path, LogRecord(base + timedelta(minutes=2*i), "Chrome", "[]", 15, None, "sample", None))
    print("Sample data inserted.")


if __name__ == "__main__":
    main()


