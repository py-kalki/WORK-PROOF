from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd  # type: ignore

from .database import db_session


def _bounds(d0: date, d1: date) -> tuple[datetime, datetime]:
    start = datetime.combine(d0, time.min).replace(tzinfo=timezone.utc)
    end = datetime.combine(d1, time.max).replace(tzinfo=timezone.utc)
    return start, end


def load_samples_df(db_path: Path, start: datetime, end: datetime) -> pd.DataFrame:
    with db_session(db_path) as conn:
        df = pd.read_sql_query(
            """
            SELECT timestamp, active_app, idle_seconds
            FROM logs
            WHERE event_type='sample' AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
            """,
            conn,
            params=(start.isoformat(), end.isoformat()),
            parse_dates=["timestamp"],
        )
    return df


def daily_active_seconds(df: pd.DataFrame, sampling_interval: int, idle_threshold: int) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["date", "active_seconds"])
    df = df.copy()
    df["date"] = df["timestamp"].dt.date
    df["is_active"] = df["idle_seconds"] < idle_threshold
    agg = df.groupby("date")["is_active"].sum().reset_index(name="active_samples")
    agg["active_seconds"] = agg["active_samples"] * sampling_interval
    return agg[["date", "active_seconds"]]


def app_usage_seconds(df: pd.DataFrame, sampling_interval: int) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["app", "seconds"])
    df = df.copy()
    df["app"] = df["active_app"].fillna("Unknown")
    agg = df.groupby("app")["timestamp"].count().reset_index(name="samples")
    agg["seconds"] = agg["samples"] * sampling_interval
    return agg[["app", "seconds"]].sort_values("seconds", ascending=False)


