from __future__ import annotations

import collections
from dataclasses import dataclass
from datetime import date, datetime, time, timezone, timedelta
from typing import Dict, Iterable, List, Tuple

from .database import fetch_logs_between


@dataclass
class DailySummary:
    date: date
    total_samples: int
    total_idle_seconds: int
    app_time: Dict[str, int]  # app -> approximate seconds active (sampling * interval)
    project_events: Dict[str, int]  # project_path -> event count
    top_apps: List[Tuple[str, int]]


def summarize_day(db_path, day: date, sampling_interval_seconds: int) -> DailySummary:
    start = datetime.combine(day, time.min).replace(tzinfo=timezone.utc)
    end = datetime.combine(day, time.max).replace(tzinfo=timezone.utc)
    logs = list(fetch_logs_between(db_path, start, end))
    total_samples = 0
    total_idle = 0
    app_counts: Dict[str, int] = collections.Counter()
    proj_events: Dict[str, int] = collections.Counter()
    for row in logs:
        et = row["event_type"]
        if et == "sample":
            total_samples += 1
            total_idle += int(row.get("idle_seconds") or 0)
            app = row.get("active_app") or "Unknown"
            app_counts[app] += 1
        elif et.startswith("file_"):
            proj = row.get("project_path") or "Unknown"
            proj_events[proj] += 1
    app_time = {k: v * sampling_interval_seconds for k, v in app_counts.items()}
    top_apps = sorted(app_time.items(), key=lambda x: x[1], reverse=True)[:10]
    return DailySummary(
        date=day,
        total_samples=total_samples,
        total_idle_seconds=total_idle,
        app_time=app_time,
        project_events=proj_events,
        top_apps=top_apps,
    )



