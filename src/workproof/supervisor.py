from __future__ import annotations

import logging
import threading
import time
from typing import Optional

import schedule  # type: ignore

from .config import Config
from .database import purge_older_than
from .file_watcher import FileWatcher
from .proofs import ProofOptions, capture_proof
from .tracker import Tracker

LOGGER = logging.getLogger(__name__)


class Supervisor:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.tracker = Tracker(cfg, cfg.db_path)
        self.watcher = FileWatcher(cfg.projects_dir, cfg.db_path, ignored_globs=cfg.ignored_globs)
        self.stop_event = threading.Event()
        self._sched_thread: Optional[threading.Thread] = None
        self._paused = False
        self._running = False

    def start(self) -> None:
        if self.is_running():
            return
        self.watcher.start()
        self.tracker.start()
        self._running = True
        # schedule jobs
        schedule.clear()
        schedule.every().day.at("03:10").do(lambda: purge_older_than(self.cfg.db_path, self.cfg.retention_days))
        schedule.every(self.cfg.proof_interval_minutes).minutes.do(
            lambda: capture_proof(self.cfg, ProofOptions(self.cfg.proof_blur_radius, self.cfg.proof_watermark))
        )
        self._sched_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._sched_thread.start()

    def _run_scheduler(self) -> None:
        while not self.stop_event.is_set():
            schedule.run_pending()
            time.sleep(0.5)

    def pause(self) -> None:
        self._paused = True
        self.tracker.pause()

    def resume(self) -> None:
        self._paused = False
        self.tracker.resume()

    def stop(self) -> None:
        self.stop_event.set()
        self.tracker.stop()
        self.watcher.stop()
        self.tracker.join(timeout=2)
        if self._sched_thread and self._sched_thread.is_alive():
            # give scheduler loop a moment to exit
            time.sleep(0.6)
        self._running = False

    def is_running(self) -> bool:
        return bool(self._running and self.tracker.is_alive())

    def is_paused(self) -> bool:
        return self._paused


