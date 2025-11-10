from __future__ import annotations

from datetime import date
from pathlib import Path

from src.workproof.config import default_config
from src.workproof.report_generator import generate_report_html, try_export_pdf


def main() -> None:
    cfg = default_config()
    out_html = cfg.reports_dir / f"report_{date.today().isoformat()}.html"
    html = generate_report_html(out_html, date.today(), cfg.sampling_interval_seconds, Path("assets/templates"), cfg.db_path)
    pdf_path = cfg.reports_dir / f"report_{date.today().isoformat()}.pdf"
    try_export_pdf(out_html, pdf_path)
    print(out_html)


if __name__ == "__main__":
    main()


