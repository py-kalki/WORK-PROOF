from __future__ import annotations

import base64
import io
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional, Tuple

import click
import matplotlib.pyplot as plt  # type: ignore
from jinja2 import Environment, FileSystemLoader, select_autoescape  # type: ignore

from .config import default_config
from .summarizer import summarize_day

LOGGER = logging.getLogger(__name__)


def _chart_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    data = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{data}"


def generate_report_html(output_html: Path, day: date, sampling_interval: int, templates_dir: Path, db_path: Path) -> str:
    summary = summarize_day(db_path, day, sampling_interval)
    # Chart: top apps
    labels = [a for a, _ in summary.top_apps] or ["No Data"]
    values = [s for _, s in summary.top_apps] or [0]
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.barh(labels, values)
    ax.set_title("Top Applications (seconds)")
    ax.invert_yaxis()
    chart1 = _chart_to_base64(fig)

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    tmpl = env.get_template("report.html.jinja2")
    html = tmpl.render(
        day=str(day),
        summary=summary,
        chart_apps=chart1,
    )
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(html, encoding="utf-8")
    return html


def try_export_pdf(html_path: Path, pdf_path: Path) -> bool:
    # Try WeasyPrint first
    try:
        from weasyprint import HTML  # type: ignore

        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        return True
    except Exception as e:
        LOGGER.warning("WeasyPrint not available or failed: %s", e)
    # Try pdfkit + wkhtmltopdf
    try:
        import pdfkit  # type: ignore
        import os
        wk = os.environ.get("WKHTMLTOPDF_PATH")
        cfg = pdfkit.configuration(wkhtmltopdf=wk) if wk else None

        pdfkit.from_file(str(html_path), str(pdf_path), configuration=cfg)
        return True
    except Exception as e:
        LOGGER.warning("pdfkit/wkhtmltopdf not available or failed: %s", e)
    # Fallback: ReportLab render simple text with link to HTML
    try:
        from reportlab.lib.pagesizes import letter  # type: ignore
        from reportlab.pdfgen import canvas  # type: ignore

        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.setFont("Helvetica", 12)
        c.drawString(72, 720, "WorkProof Report")
        c.drawString(72, 700, f"See HTML: {html_path}")
        c.showPage()
        c.save()
        return True
    except Exception as e:
        LOGGER.warning("ReportLab fallback failed: %s", e)
        return False


def _format_seconds(secs: int) -> str:
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def generate_text_summary(day: date, sampling_interval: int, db_path: Path, idle_threshold: int = 60) -> str:
    summary = summarize_day(db_path, day, sampling_interval)
    active_samples = summary.total_samples  # will filter by idle below in a query-light approximation
    # Approx active seconds by discounting portions of idle; here we approximate via thresholding in code
    # Note: For precision, use SQL filters by idle threshold. Simplified here for CLI text output.
    # Active time approximation: assume fraction active = 1 - (total_idle / (samples * interval)), clamp to [0,1]
    denom = max(1, summary.total_samples * sampling_interval)
    frac_active = max(0.0, min(1.0, 1.0 - (summary.total_idle_seconds / denom)))
    approx_active_seconds = int(denom * frac_active)
    top_apps_text = ", ".join(f"{app} ({_format_seconds(sec)})" for app, sec in summary.top_apps[:5])
    top_projects = sorted(summary.project_events.items(), key=lambda x: x[1], reverse=True)[:5]
    top_projects_text = ", ".join(f"{p} ({n})" for p, n in top_projects) if top_projects else "None"
    text = (
        f"Date: {day.isoformat()}\n"
        f"Active time (approx): {_format_seconds(approx_active_seconds)}\n"
        f"Idle time (sum): {_format_seconds(summary.total_idle_seconds)}\n"
        f"Top apps: {top_apps_text or 'None'}\n"
        f"File activity: {top_projects_text}\n"
    )
    return text


@click.command()
@click.option("--date", "date_arg", default="today", help="Date in YYYY-MM-DD or 'today'")
@click.option("--out", "out_html", default=None, help="Output HTML path")
@click.option("--pdf", "out_pdf", default=None, help="Optional PDF output path")
@click.option("--text", "as_text", is_flag=True, help="Print a basic text summary to stdout")
def cli(date_arg: str, out_html: Optional[str], out_pdf: Optional[str], as_text: bool) -> None:
    cfg = default_config()
    if date_arg == "today":
        d = date.today()
    else:
        d = datetime.strptime(date_arg, "%Y-%m-%d").date()
    if as_text:
        click.echo(generate_text_summary(d, cfg.sampling_interval_seconds, cfg.db_path, cfg.idle_threshold_seconds))
        return
    else:
        out_html_path = Path(out_html) if out_html else (cfg.reports_dir / f"report_{d.isoformat()}.html")
        templates_dir = Path("assets/templates")
        html = generate_report_html(out_html_path, d, cfg.sampling_interval_seconds, templates_dir, cfg.db_path)
        if out_pdf:
            pdf_ok = try_export_pdf(out_html_path, Path(out_pdf))
            LOGGER.info("PDF export %s", "ok" if pdf_ok else "skipped")
        click.echo(str(out_html_path))


if __name__ == "__main__":
    cli()



