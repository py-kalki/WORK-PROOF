from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, Optional, Tuple

LOGGER = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 2


@dataclass
class LogRecord:
    timestamp: datetime
    active_app: Optional[str]
    running_apps: str  # JSON list
    idle_seconds: int
    project_path: Optional[str]
    event_type: str  # 'sample' | 'file_event'
    meta: Optional[str]  # JSON object


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), timeout=10, isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


@contextmanager
def db_session(path: Path) -> Generator[sqlite3.Connection, None, None]:
    conn = _connect(path)
    try:
        yield conn
    finally:
        conn.close()


def initialize(path: Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with db_session(path) as conn:
        conn.execute("BEGIN")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                active_app TEXT,
                running_apps TEXT NOT NULL,
                idle_seconds INTEGER NOT NULL,
                project_path TEXT,
                event_type TEXT NOT NULL,
                meta TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_event_type ON logs(event_type)")
        version = _get_schema_version(conn)
        if version is None:
            _set_schema_version(conn, 1)
            version = 1
        # migrations
        if version < 2:
            _migrate_to_v2(conn)
            _set_schema_version(conn, 2)
        conn.execute("COMMIT")


def _get_schema_version(conn: sqlite3.Connection) -> Optional[int]:
    cur = conn.execute("SELECT value FROM meta WHERE key='schema_version'")
    row = cur.fetchone()
    return int(row[0]) if row else None


def _set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version', ?)", (str(version),))


def _migrate_to_v2(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            main_app TEXT,
            samples INTEGER NOT NULL DEFAULT 0,
            idle_seconds INTEGER NOT NULL DEFAULT 0,
            files_edited INTEGER NOT NULL DEFAULT 0,
            proofs_count INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS session_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            ref_log_id INTEGER
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_time)")


def insert_log(path: Path, record: LogRecord) -> None:
    payload: Tuple[Any, ...] = (
        record.timestamp.replace(tzinfo=timezone.utc).isoformat(),
        record.active_app,
        record.running_apps,
        record.idle_seconds,
        record.project_path,
        record.event_type,
        record.meta,
    )
    for attempt in range(3):
        try:
            with db_session(path) as conn:
                conn.execute(
                    """
                    INSERT INTO logs(timestamp, active_app, running_apps, idle_seconds, project_path, event_type, meta)
                    VALUES(?,?,?,?,?,?,?)
                    """,
                    payload,
                )
            return
        except sqlite3.OperationalError as e:
            LOGGER.warning("DB insert retry %s due to %s", attempt + 1, e)
    # final attempt raise
    with db_session(path) as conn:
        conn.execute(
            """
            INSERT INTO logs(timestamp, active_app, running_apps, idle_seconds, project_path, event_type, meta)
            VALUES(?,?,?,?,?,?,?)
            """,
            payload,
        )


def purge_older_than(path: Path, days: int) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    with db_session(path) as conn:
        cur = conn.execute("DELETE FROM logs WHERE timestamp < ?", (cutoff.isoformat(),))
        conn.execute("VACUUM")
        return cur.rowcount


def fetch_logs_between(path: Path, start: datetime, end: datetime) -> Iterable[Dict[str, Any]]:
    with db_session(path) as conn:
        cur = conn.execute(
            """
            SELECT timestamp, active_app, running_apps, idle_seconds, project_path, event_type, meta
            FROM logs
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
            """,
            (start.isoformat(), end.isoformat()),
        )
        cols = [c[0] for c in cur.description]
        for row in cur.fetchall():
            d = dict(zip(cols, row))
            # parse JSON fields
            try:
                d["running_apps"] = json.loads(d["running_apps"])
            except Exception:
                pass
            try:
                d["meta"] = json.loads(d["meta"]) if d["meta"] else None
            except Exception:
                pass
            return_item = d
            yield return_item



