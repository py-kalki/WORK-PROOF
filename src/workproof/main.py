from __future__ import annotations

import logging
import signal
import sys
import threading
import time
from datetime import datetime, timezone
import os

import schedule  # type: ignore

from .config import default_config
from .database import initialize, purge_older_than
from .file_watcher import FileWatcher
from .proofs import ProofOptions, capture_proof
from .tracker import Tracker
from .backup import backup_all
from .utils.logging_setup import setup_logging

LOGGER = logging.getLogger(__name__)


def _setup() -> tuple:
    cfg = default_config()
    setup_logging(cfg.logs_dir)
    initialize(cfg.db_path)
    return cfg


def main() -> int:
    cfg = _setup()
    tracker = Tracker(cfg, cfg.db_path)
    watcher = FileWatcher(cfg.projects_dir, cfg.db_path, ignored_globs=cfg.ignored_globs)

    # Retention schedule (daily)
    schedule.every().day.at("03:10").do(lambda: purge_older_than(cfg.db_path, cfg.retention_days))
    # Proof capture schedule
    schedule.every(cfg.proof_interval_minutes).minutes.do(
        lambda: capture_proof(cfg, ProofOptions(cfg.proof_blur_radius, cfg.proof_watermark))
    )
    # Optional weekly backup on Sunday 04:00 - requires env WORKPROOF_BACKUP_PW
    schedule.every().sunday.at("04:00").do(
        lambda: (os.getenv("WORKPROOF_BACKUP_PW") and backup_all(cfg, os.getenv("WORKPROOF_BACKUP_PW") or ""))
    )

    stop_event = threading.Event()

    def handle_sig(signum, frame):
        LOGGER.info("Signal %s received, stopping...", signum)
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, handle_sig)
        except Exception:
            pass

    try:
        watcher.start()
        tracker.start()
        LOGGER.info("WorkProof running. Silent=%s", cfg.silent)
        while not stop_event.is_set():
            schedule.run_pending()
            time.sleep(0.5)
    finally:
        tracker.stop()
        watcher.stop()
        tracker.join(timeout=2)
    LOGGER.info("Shutdown complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



