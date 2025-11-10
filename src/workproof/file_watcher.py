from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Iterable

from watchdog.events import FileSystemEventHandler, FileSystemEvent  # type: ignore
from watchdog.observers import Observer  # type: ignore

from .database import LogRecord, insert_log

LOGGER = logging.getLogger(__name__)


class ProjectFileEventHandler(FileSystemEventHandler):
    def __init__(self, db_path: Path, root: Path, ignored_globs: Iterable[str] | None = None) -> None:
        super().__init__()
        self.db_path = db_path
        self.root = root
        self.ignored_globs = tuple(ignored_globs or ())

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        if self._is_ignored(event.src_path):
            return
        ev_type = "modified"
        if event.event_type == "created":
            ev_type = "created"
        elif event.event_type == "deleted":
            ev_type = "deleted"
        meta = {
            "src_path": str(event.src_path),
        }
        ts = datetime.now(timezone.utc)
        rec = LogRecord(
            timestamp=ts,
            active_app=None,
            running_apps="[]",
            idle_seconds=0,
            project_path=str(self._project_for(event.src_path)),
            event_type=f"file_{ev_type}",
            meta=json.dumps(meta, ensure_ascii=False),
        )
        insert_log(self.db_path, rec)

    def _project_for(self, path: str) -> Path:
        try:
            p = Path(path)
            # project == immediate child dir of root, else root
            rel = p.relative_to(self.root)
            if len(rel.parts) > 0:
                return self.root / rel.parts[0]
        except Exception:
            pass
        return self.root
    
    def _is_ignored(self, path: str) -> bool:
        p = Path(path)
        parts = set(p.parts)
        for g in self.ignored_globs:
            if g in parts:
                return True
        return False


class FileWatcher:
    def __init__(self, projects_dir: Path, db_path: Path, ignored_globs: Iterable[str] | None = None) -> None:
        self.projects_dir = projects_dir
        self.db_path = db_path
        self.handler = ProjectFileEventHandler(db_path, projects_dir, ignored_globs=ignored_globs)
        self.observer = Observer()

    def start(self) -> None:
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.observer.schedule(self.handler, str(self.projects_dir), recursive=True)
        self.observer.start()
        LOGGER.info("File watcher started at %s", self.projects_dir)

    def stop(self) -> None:
        try:
            self.observer.stop()
            self.observer.join(timeout=2)
        except Exception:
            pass
        LOGGER.info("File watcher stopped")



