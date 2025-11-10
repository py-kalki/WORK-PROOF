from __future__ import annotations

import base64
import io
from typing import Dict, Any

import matplotlib.pyplot as plt  # type: ignore
import seaborn as sns  # type: ignore


def fig_to_data_uri(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def build_bar_daily_hours(dates, seconds) -> str:
    fig, ax = plt.subplots(figsize=(6, 3))
    hours = [s / 3600 for s in seconds]
    bars = ax.bar(range(len(dates)), hours, color="#52129e")
    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels(dates, rotation=45, ha="right")
    ax.set_title("Daily Active Hours")
    ax.set_ylabel("Hours")
    # annotate values
    for i, b in enumerate(bars):
        val = hours[i]
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.05, f"{val:.1f}h", ha="center", va="bottom", fontsize=8, color="#333")
    return fig_to_data_uri(fig)


def build_pie_app_usage(labels, seconds) -> str:
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(seconds, labels=labels, autopct="%1.0f%%")
    ax.set_title("App Usage Share")
    return fig_to_data_uri(fig)


def build_line_weekly_trend(dates, seconds) -> str:
    fig, ax = plt.subplots(figsize=(6, 3))
    hours = [s / 3600 for s in seconds]
    ax.plot(dates, hours, marker="o", color="#16101e")
    ax.set_title("Weekly Productivity Trend")
    ax.set_ylabel("Hours")
    ax.grid(True, alpha=0.3)
    return fig_to_data_uri(fig)


