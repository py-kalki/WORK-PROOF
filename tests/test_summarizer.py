from __future__ import annotations

from datetime import date, datetime, timezone, timedelta
from pathlib import Path
import tempfile

from src.workproof.database import initialize, insert_log, LogRecord
from src.workproof.summarizer import summarize_day


def test_summarize_day_counts_samples_and_top_apps():
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "test.db"
        initialize(db)
        today = date.today()
        base = datetime.now(timezone.utc).replace(hour=10, minute=0, second=0, microsecond=0)
        for i in range(5):
            insert_log(db, LogRecord(base + timedelta(seconds=i*10), "VSCode", "[]", 0, None, "sample", None))
        for i in range(3):
            insert_log(db, LogRecord(base + timedelta(seconds=100 + i*10), "Chrome", "[]", 0, None, "sample", None))
        summary = summarize_day(db, today, 10)
        assert summary.total_samples >= 8
        top = dict(summary.top_apps)
        assert "VSCode" in top
        assert top["VSCode"] >= top.get("Chrome", 0)



