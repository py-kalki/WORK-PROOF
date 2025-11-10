from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pynput import keyboard, mouse  # type: ignore

from .config import Config
from .database import LogRecord, insert_log
from .utils.platform_adapters import get_active_window_title, processes_json

LOGGER = logging.getLogger(__name__)


class IdleDetector:
    def __init__(self) -> None:
        self._last_input_time = time.time()
        self._kb_listener = keyboard.Listener(on_press=self._on_input, on_release=self._on_input)
        self._mouse_listener = mouse.Listener(on_move=self._on_input, on_click=self._on_input, on_scroll=self._on_input)

    def _on_input(self, *args, **kwargs) -> None:
        self._last_input_time = time.time()

    def start(self) -> None:
        self._kb_listener.start()
        self._mouse_listener.start()

    def stop(self) -> None:
        try:
            self._kb_listener.stop()
        except Exception:
            pass
        try:
            self._mouse_listener.stop()
        except Exception:
            pass

    def idle_seconds(self) -> int:
        return int(time.time() - self._last_input_time)


class Tracker(threading.Thread):
    def __init__(self, cfg: Config, db_path: Path) -> None:
        super().__init__(daemon=True)
        self.cfg = cfg
        self.db_path = db_path
        self._stop_event = threading.Event()
        self._paused = threading.Event()
        self._paused.clear()
        self._idle = IdleDetector()

    def pause(self) -> None:
        self._paused.set()

    def resume(self) -> None:
        self._paused.clear()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        self._idle.start()
        LOGGER.info("Tracker started with interval %ss", self.cfg.sampling_interval_seconds)
        try:
            while not self._stop_event.is_set():
                if self._paused.is_set():
                    time.sleep(0.5)
                    continue
                self.sample_once()
                time.sleep(self.cfg.sampling_interval_seconds)
        finally:
            self._idle.stop()
            LOGGER.info("Tracker stopped")

    def sample_once(self) -> None:
        ts = datetime.now(timezone.utc)
        active = get_active_window_title()
        running = processes_json(limit=50)
        idle_s = self._idle.idle_seconds()
        meta = {"idle_threshold": self.cfg.idle_threshold_seconds}
        rec = LogRecord(
            timestamp=ts,
            active_app=active,
            running_apps=running,
            idle_seconds=idle_s,
            project_path=None,
            event_type="sample",
            meta=json.dumps(meta, ensure_ascii=False),
        )
        insert_log(self.db_path, rec)



