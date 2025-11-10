from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import tempfile

from src.workproof.database import initialize, insert_log, LogRecord
from src.workproof.sessions import build_sessions_for_day
from src.workproof.dashboard import q_active_seconds, q_top_apps, day_bounds_utc


def test_sessions_and_active_seconds_basic():
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "test.db"
        initialize(db)
        start = datetime.now(timezone.utc).replace(hour=9, minute=0, second=0, microsecond=0)
        # 6 active samples (idle < threshold) and 2 idle samples
        for i in range(6):
            insert_log(db, LogRecord(start + timedelta(seconds=i*10), "VSCode", "[]", 0, None, "sample", None))
        for i in range(2):
            insert_log(db, LogRecord(start + timedelta(seconds=100 + i*10), "Chrome", "[]", 600, None, "sample", None))
        # one file event and one proof
        insert_log(db, LogRecord(start + timedelta(seconds=30), None, "[]", 0, "ProjA", "file_modified", None))
        insert_log(db, LogRecord(start + timedelta(seconds=35), "VSCode", "[]", 0, None, "proof_capture", None))
        day = start.date()
        s, e = day_bounds_utc(day)
        sessions = build_sessions_for_day(db, s, e, 10, 60, 300)
        assert len(sessions) >= 1
        act = q_active_seconds(db, s, e, 10, 60)
        assert act >= 60


