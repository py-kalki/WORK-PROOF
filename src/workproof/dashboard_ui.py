from __future__ import annotations

import tkinter as tk
from datetime import date, timedelta
from pathlib import Path

from .analytics import load_samples_df, daily_active_seconds, app_usage_seconds
from .charts_builder import build_bar_daily_hours, build_pie_app_usage, build_line_weekly_trend
from .config import default_config


class DashboardApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("WorkProof Analytics")
        self.configure(bg="#16101e")
        self.geometry("900x600")
        self.cfg = default_config()
        self._build()
        self._refresh()

    def _build(self) -> None:
        self.lbl_title = tk.Label(self, text="Analytics Dashboard", bg="#16101e", fg="white", font=("Segoe UI", 16, "bold"))
        self.lbl_title.pack(pady=10)
        self.panel = tk.Text(self, bg="white", fg="black", height=30)
        self.panel.pack(fill="both", expand=True, padx=10, pady=10)

    def _refresh(self) -> None:
        d1 = date.today() - timedelta(days=6)
        d2 = date.today()
        start, end = d1, d2
        df = load_samples_df(self.cfg.db_path, *self._bounds(d1, d2))
        daily = daily_active_seconds(df, self.cfg.sampling_interval_seconds, self.cfg.idle_threshold_seconds)
        apps = app_usage_seconds(df, self.cfg.sampling_interval_seconds).head(8)
        bar_uri = build_bar_daily_hours(daily["date"].astype(str).tolist(), daily["active_seconds"].tolist())
        pie_uri = build_pie_app_usage(apps["app"].tolist(), apps["seconds"].tolist())
        trend_uri = build_line_weekly_trend(daily["date"].astype(str).tolist(), daily["active_seconds"].tolist())
        self.panel.delete("1.0", tk.END)
        self.panel.insert(tk.END, f"Daily Bar: {bar_uri}\n\nPie Apps: {pie_uri}\n\nWeekly Trend: {trend_uri}\n")

    @staticmethod
    def _bounds(d0: date, d1: date):
        from datetime import datetime, time, timezone
        start = datetime.combine(d0, time.min).replace(tzinfo=timezone.utc)
        end = datetime.combine(d1, time.max).replace(tzinfo=timezone.utc)
        return start, end


if __name__ == "__main__":
    app = DashboardApp()
    app.mainloop()


