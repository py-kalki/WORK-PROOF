from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path

import tempfile

from src.workproof.database import initialize, insert_log, LogRecord, fetch_logs_between, purge_older_than


def test_insert_and_fetch():
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "test.db"
        initialize(db)
        ts = datetime.now(timezone.utc)
        rec = LogRecord(ts, "App", "[]", 0, None, "sample", None)
        insert_log(db, rec)
        rows = list(fetch_logs_between(db, ts - timedelta(seconds=1), ts + timedelta(seconds=1)))
        assert len(rows) == 1
        assert rows[0]["active_app"] == "App"


def test_purge():
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "test.db"
        initialize(db)
        ts_old = datetime.now(timezone.utc) - timedelta(days=90)
        rec_old = LogRecord(ts_old, "Old", "[]", 0, None, "sample", None)
        insert_log(db, rec_old)
        purged = purge_older_than(db, 60)
        assert purged >= 1



