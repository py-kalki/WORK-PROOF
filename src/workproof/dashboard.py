from __future__ import annotations

import json
import logging
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Dict, Any, List

import click

from .config import default_config
from .database import db_session
from .sessions import build_sessions_for_day

LOGGER = logging.getLogger(__name__)


def day_bounds_utc(d: date) -> tuple[datetime, datetime]:
    start = datetime.combine(d, time.min).replace(tzinfo=timezone.utc)
    end = datetime.combine(d, time.max).replace(tzinfo=timezone.utc)
    return start, end


def q_active_seconds(db_path: Path, start: datetime, end: datetime, interval: int, idle_threshold: int) -> int:
    with db_session(db_path) as conn:
        cur = conn.execute(
            """
            SELECT COUNT(*) FROM logs
            WHERE event_type='sample' AND timestamp BETWEEN ? AND ? AND idle_seconds < ?
            """,
            (start.isoformat(), end.isoformat(), idle_threshold),
        )
        n = int(cur.fetchone()[0])
    return n * interval


def q_idle_sum(db_path: Path, start: datetime, end: datetime) -> int:
    with db_session(db_path) as conn:
        cur = conn.execute(
            """
            SELECT COALESCE(SUM(idle_seconds),0) FROM logs
            WHERE event_type='sample' AND timestamp BETWEEN ? AND ?
            """,
            (start.isoformat(), end.isoformat()),
        )
        return int(cur.fetchone()[0] or 0)


def q_top_apps(db_path: Path, start: datetime, end: datetime, interval: int) -> List[Dict[str, Any]]:
    with db_session(db_path) as conn:
        cur = conn.execute(
            """
            SELECT COALESCE(active_app,'Unknown') as app, COUNT(*) as cnt
            FROM logs
            WHERE event_type='sample' AND timestamp BETWEEN ? AND ?
            GROUP BY app ORDER BY cnt DESC LIMIT 10
            """,
            (start.isoformat(), end.isoformat()),
        )
        return [{"app": r[0], "seconds": int(r[1]) * interval} for r in cur.fetchall()]


def q_top_projects(db_path: Path, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    with db_session(db_path) as conn:
        cur = conn.execute(
            """
            SELECT COALESCE(project_path,'Unknown') as proj, COUNT(*) as cnt
            FROM logs
            WHERE event_type LIKE 'file_%' AND timestamp BETWEEN ? AND ?
            GROUP BY proj ORDER BY cnt DESC LIMIT 10
            """,
            (start.isoformat(), end.isoformat()),
        )
        return [{"project": r[0], "events": int(r[1])} for r in cur.fetchall()]


def q_proofs_count(db_path: Path, start: datetime, end: datetime) -> int:
    with db_session(db_path) as conn:
        cur = conn.execute(
            """
            SELECT COUNT(*) FROM logs
            WHERE event_type='proof_capture' AND timestamp BETWEEN ? AND ?
            """,
            (start.isoformat(), end.isoformat()),
        )
        return int(cur.fetchone()[0] or 0)


@click.command()
@click.option("--date", "date_arg", default="today", help="Date in YYYY-MM-DD or 'today'")
@click.option("--json", "json_out", default=None, help="Output JSON file path")
def cli(date_arg: str, json_out: str | None) -> None:
    cfg = default_config()
    d = date.today() if date_arg == "today" else datetime.strptime(date_arg, "%Y-%m-%d").date()
    start, end = day_bounds_utc(d)
    active_seconds = q_active_seconds(cfg.db_path, start, end, cfg.sampling_interval_seconds, cfg.idle_threshold_seconds)
    idle_seconds = q_idle_sum(cfg.db_path, start, end)
    top_apps = q_top_apps(cfg.db_path, start, end, cfg.sampling_interval_seconds)
    top_projects = q_top_projects(cfg.db_path, start, end)
    proofs_count = q_proofs_count(cfg.db_path, start, end)
    sessions = build_sessions_for_day(cfg.db_path, start, end, cfg.sampling_interval_seconds, cfg.idle_threshold_seconds, cfg.session_gap_seconds)
    payload = {
        "date": d.isoformat(),
        "active_seconds": active_seconds,
        "idle_seconds": idle_seconds,
        "top_apps": top_apps,
        "top_projects": top_projects,
        "proofs_count": proofs_count,
        "sessions": [
            {
                "start": s.start_time.isoformat(),
                "end": (s.end_time.isoformat() if s.end_time else None),
                "main_app": s.main_app,
                "samples": s.samples,
                "files_edited": s.files_edited,
                "proofs_count": s.proofs_count,
            }
            for s in sessions
        ],
    }
    if json_out:
        out = Path(json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        click.echo(str(out))
    else:
        click.echo(json.dumps(payload, indent=2))


if __name__ == "__main__":
    cli()


