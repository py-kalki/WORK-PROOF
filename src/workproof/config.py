from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from platformdirs import user_data_dir


APP_NAME = "WorkProof"
APP_AUTHOR = "WorkProofProject"


@dataclass(frozen=True)
class Config:
    db_path: Path
    projects_dir: Path
    logs_dir: Path
    reports_dir: Path
    proofs_dir: Path | None = None
    sampling_interval_seconds: int = 10
    flush_interval_seconds: int = 30
    retention_days: int = 60
    idle_threshold_seconds: int = 60
    silent: bool = True
    ignored_globs: tuple[str, ...] = (".git", "node_modules", "__pycache__", "build", "dist")
    proof_interval_minutes: int = 10
    session_gap_seconds: int = 300
    proof_blur_radius: int = 8
    proof_watermark: bool = True


def default_config(overrides: Optional[dict] = None) -> Config:
    base_dir = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    db_path = base_dir / "workproof.db"
    projects_dir = Path.home() / "Projects"
    logs_dir = base_dir / "logs"
    reports_dir = base_dir / "reports"
    proofs_dir = base_dir / "Proofs"
    base_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    proofs_dir.mkdir(parents=True, exist_ok=True)
    cfg = Config(
        db_path=db_path,
        projects_dir=projects_dir,
        logs_dir=logs_dir,
        reports_dir=reports_dir,
        proofs_dir=proofs_dir,
    )
    if overrides:
        return Config(**{**cfg.__dict__, **overrides})
    return cfg



