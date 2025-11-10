from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import sqlite3

from .config import Config
from .database import db_session

LOGGER = logging.getLogger(__name__)


@dataclass
class SessionRow:
    id: Optional[int]
    start_time: datetime
    end_time: Optional[datetime]
    main_app: Optional[str]
    samples: int
    idle_seconds: int
    files_edited: int
    proofs_count: int


def insert_session_row(db_path: Path, s: SessionRow) -> int:
    with db_session(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO sessions(start_time, end_time, main_app, samples, idle_seconds, files_edited, proofs_count)
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                s.start_time.isoformat(),
                s.end_time.isoformat() if s.end_time else None,
                s.main_app,
                s.samples,
                s.idle_seconds,
                s.files_edited,
                s.proofs_count,
            ),
        )
        return int(cur.lastrowid)


def update_session_row(db_path: Path, s: SessionRow) -> None:
    if s.id is None:
        raise ValueError("Session id required")
    with db_session(db_path) as conn:
        conn.execute(
            """
            UPDATE sessions
            SET end_time=?, main_app=?, samples=?, idle_seconds=?, files_edited=?, proofs_count=?
            WHERE id=?
            """,
            (
                s.end_time.isoformat() if s.end_time else None,
                s.main_app,
                s.samples,
                s.idle_seconds,
                s.files_edited,
                s.proofs_count,
                s.id,
            ),
        )


def build_sessions_for_day(db_path: Path, day_start: datetime, day_end: datetime, sampling_interval: int, idle_threshold: int, session_gap_seconds: int) -> list[SessionRow]:
    # Stateless sessionization built from logs; safe and robust
    with db_session(db_path) as conn:
        cur = conn.execute(
            """
            SELECT timestamp, active_app, idle_seconds, event_type
            FROM logs
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
            """,
            (day_start.isoformat(), day_end.isoformat()),
        )
        rows = cur.fetchall()
    sessions: list[SessionRow] = []
    current: Optional[SessionRow] = None
    last_active_ts: Optional[datetime] = None
    for ts_s, app, idle_s, et in rows:
        ts = datetime.fromisoformat(ts_s)
        if et == "sample":
            is_active = int(idle_s or 0) < idle_threshold
            if is_active:
                if current is None:
                    current = SessionRow(
                        id=None, start_time=ts, end_time=None, main_app=app or current.main_app if current else app,
                        samples=0, idle_seconds=0, files_edited=0, proofs_count=0
                    )
                current.samples += 1
                current.main_app = app or current.main_app
                last_active_ts = ts
            else:
                if current and last_active_ts and (ts - last_active_ts).total_seconds() > session_gap_seconds:
                    current.end_time = last_active_ts
                    sessions.append(current)
                    current = None
        elif et.startswith("file_"):
            if current:
                current.files_edited += 1
        elif et == "proof_capture":
            if current:
                current.proofs_count += 1
    if current:
        current.end_time = last_active_ts or current.start_time
        sessions.append(current)
    return sessions


