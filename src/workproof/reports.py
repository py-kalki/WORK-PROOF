from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, time, timezone, timedelta
from pathlib import Path
from typing import Optional

import click
import pandas as pd  # type: ignore
from jinja2 import Environment, FileSystemLoader, select_autoescape  # type: ignore

from .analytics import load_samples_df, daily_active_seconds, app_usage_seconds
from .charts_builder import build_bar_daily_hours, build_line_weekly_trend, build_pie_app_usage
from .config import default_config
from .report_generator import try_export_pdf
from reportlab.lib.pagesizes import letter  # type: ignore
from reportlab.pdfgen import canvas  # type: ignore
import base64, io


def _bounds(d0: date, d1: date):
    start = datetime.combine(d0, time.min).replace(tzinfo=timezone.utc)
    end = datetime.combine(d1, time.max).replace(tzinfo=timezone.utc)
    return start, end


def client_report(cfg, start_d: date, end_d: date, project: Optional[str] = None) -> Path:
    start, end = _bounds(start_d, end_d)
    df = load_samples_df(cfg.db_path, start, end)
    daily = daily_active_seconds(df, cfg.sampling_interval_seconds, cfg.idle_threshold_seconds)
    apps = app_usage_seconds(df, cfg.sampling_interval_seconds).head(10)
    charts = {
        "bar_daily": build_bar_daily_hours(daily["date"].astype(str).tolist(), daily["active_seconds"].tolist()),
        "line_weekly": build_line_weekly_trend(daily["date"].astype(str).tolist(), daily["active_seconds"].tolist()),
        "pie_apps": build_pie_app_usage(apps["app"].tolist(), apps["seconds"].tolist()),
    }
    env = Environment(loader=FileSystemLoader("assets/templates"), autoescape=select_autoescape(["html"]))
    html = env.get_template("client_report.html.j2").render(
        start=str(start_d), end=str(end_d), project=project or "All Projects", charts=charts,
        totals={"active_seconds": int(daily["active_seconds"].sum())}, top_apps=apps.to_dict(orient="records")
    )
    out_dir = cfg.reports_dir / f"{start_d.isoformat()}_{end_d.isoformat()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / "report.html"
    html_path.write_text(html, encoding="utf-8")
    pdf_path = out_dir / "report.pdf"
    ok = try_export_pdf(html_path, pdf_path)
    if not ok:
        # Rich fallback: embed charts and some stats directly into PDF
        _render_pdf_fallback(pdf_path, charts, int(daily["active_seconds"].sum()), apps.to_dict(orient="records"), str(start_d), str(end_d), project or "All Projects")
    (out_dir / "report.json").write_text(json.dumps({
        "start": str(start_d), "end": str(end_d), "project": project, "top_apps": apps.to_dict(orient="records")
    }, indent=2), encoding="utf-8")
    return html_path


def _render_pdf_fallback(pdf_path: Path, charts: dict, total_active: int, top_apps: list[dict], start: str, end: str, project: str) -> None:
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, "WorkProof Client Report")
    c.setFont("Helvetica", 11)
    c.drawString(72, height - 92, f"Range: {start} — {end}")
    c.drawString(72, height - 108, f"Project: {project}")
    c.drawString(72, height - 124, f"Total Active: {total_active//3600}h {(total_active%3600)//60}m")
    # Draw charts (decode base64)
    y = height - 320
    for key in ("bar_daily", "pie_apps", "line_weekly"):
        if key in charts and charts[key]:
            img_data = charts[key].split(",", 1)[-1]
            img = io.BytesIO(base64.b64decode(img_data))
            c.drawInlineImage(img, 72, y, width=width - 144, height=180, preserveAspectRatio=True)
            y -= 200
    # Top apps
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Top Apps")
    y -= 16
    c.setFont("Helvetica", 11)
    for a in top_apps[:10]:
        c.drawString(72, y, f"- {a['app']}: {a['seconds']//3600}h {(a['seconds']%3600)//60}m")
        y -= 14
        if y < 120:
            c.showPage()
            y = height - 72
    c.showPage()
    c.save()


@click.command()
@click.option("--start", "start_str", required=True, help="YYYY-MM-DD")
@click.option("--end", "end_str", required=True, help="YYYY-MM-DD")
@click.option("--project", "project", default=None, help="Project name (optional)")
def cli(start_str: str, end_str: str, project: Optional[str]) -> None:
    cfg = default_config()
    start_d = date.fromisoformat(start_str)
    end_d = date.fromisoformat(end_str)
    out = client_report(cfg, start_d, end_d, project)
    click.echo(str(out))


if __name__ == "__main__":
    cli()


