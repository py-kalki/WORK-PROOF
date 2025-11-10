from __future__ import annotations

import time
from datetime import date
from pathlib import Path
import tempfile

from src.workproof.config import default_config
from src.workproof.database import initialize
from src.workproof.file_watcher import FileWatcher
from src.workproof.report_generator import generate_report_html
from src.workproof.tracker import Tracker
from src.workproof.utils.logging_setup import setup_logging


def test_integration_end_to_end(tmp_path: Path):
    cfg = default_config({
        "sampling_interval_seconds": 2,
        "projects_dir": tmp_path / "Projects",
        "reports_dir": tmp_path / "reports",
        "logs_dir": tmp_path / "logs",
        "db_path": tmp_path / "workproof.db",
    })
    setup_logging(cfg.logs_dir)
    initialize(cfg.db_path)
    tracker = Tracker(cfg, cfg.db_path)
    watcher = FileWatcher(cfg.projects_dir, cfg.db_path)
    cfg.projects_dir.mkdir(parents=True, exist_ok=True)
    watcher.start()
    tracker.start()
    # simulate file activity
    f = cfg.projects_dir / "Demo" / "file.txt"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("hello", encoding="utf-8")
    time.sleep(1)
    f.write_text("world", encoding="utf-8")
    # let tracker run a little
    time.sleep(6)
    tracker.stop()
    watcher.stop()
    tracker.join(timeout=2)
    # generate report
    out_html = cfg.reports_dir / "test.html"
    html = generate_report_html(out_html, date.today(), cfg.sampling_interval_seconds, Path("assets/templates"), cfg.db_path)
    assert out_html.exists()
    assert "WorkProof Daily Report" in out_html.read_text(encoding="utf-8")



