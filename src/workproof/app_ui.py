from __future__ import annotations

import os
import sys
import threading
import time
from datetime import date
from pathlib import Path

import customtkinter as ctk  # type: ignore

from .autostart_win import add_startup_shortcut, remove_startup_shortcut
from .config import default_config
from .report_generator import generate_text_summary
from .reports import client_report
from .sessions import build_sessions_for_day
from .supervisor import Supervisor


class WorkProofApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.title("WorkProof")
        self.geometry("860x600")
        self.resizable(True, True)
        self.cfg = default_config()
        self.sup = Supervisor(self.cfg)
        self._build()
        # start in background
        self.sup.start()
        self._refresh_async()

    def _build(self) -> None:
        # Header with status light
        header = ctk.CTkFrame(self, corner_radius=8)
        header.pack(fill="x", padx=12, pady=8)
        self.status_dot = ctk.CTkLabel(header, text="●", font=("Segoe UI", 24))
        self.status_text = ctk.CTkLabel(header, text="Starting…", font=("Segoe UI", 16))
        self.status_dot.pack(side="left", padx=8, pady=8)
        self.status_text.pack(side="left", padx=6)

        # Controls row
        controls = ctk.CTkFrame(self, corner_radius=8)
        controls.pack(fill="x", padx=12, pady=4)
        self.btn_start = ctk.CTkButton(controls, text="Start", command=self._on_start)
        self.btn_pause = ctk.CTkButton(controls, text="Pause", command=self._on_pause)
        self.btn_resume = ctk.CTkButton(controls, text="Resume", command=self._on_resume)
        self.btn_stop = ctk.CTkButton(controls, text="Stop", command=self._on_stop)
        self.btn_report = ctk.CTkButton(controls, text="Generate Today Report", command=self._on_report_today)
        self.btn_open_reports = ctk.CTkButton(controls, text="Open Reports Folder", command=self._on_open_reports)
        for b in (self.btn_start, self.btn_pause, self.btn_resume, self.btn_stop, self.btn_report, self.btn_open_reports):
            b.pack(side="left", padx=6, pady=6)

        # Autostart row (Windows-only)
        auto = ctk.CTkFrame(self, corner_radius=8)
        auto.pack(fill="x", padx=12, pady=4)
        self.sw_autostart = ctk.CTkSwitch(auto, text="Start WorkProof at login", command=self._on_autostart_toggle)
        self.sw_autostart.pack(side="left", padx=6, pady=6)
        # initialize switch state
        self.after(200, self._init_autostart_state)

        # Main text area
        self.txt = ctk.CTkTextbox(self, width=820, height=440)
        self.txt.pack(fill="both", expand=True, padx=12, pady=8)

    def _on_start(self) -> None:
        # restart if stopped
        self.sup.stop()
        time.sleep(0.2)
        self.sup = Supervisor(self.cfg)
        self.sup.start()

    def _on_pause(self) -> None:
        self.sup.pause()

    def _on_resume(self) -> None:
        self.sup.resume()

    def _on_stop(self) -> None:
        # stop background tracking but keep UI open
        self.sup.stop()
        self._append("[Supervisor] Stopped tracking")

    def _on_report_today(self) -> None:
        # Quick HTML report for today
        today = date.today()
        p = client_report(self.cfg, today, today, project=None)
        self._append(f"[Report] Generated: {p}")

    def _on_open_reports(self) -> None:
        path = self.cfg.reports_dir
        try:
            os.startfile(str(path))  # Windows
        except Exception:
            self._append(f"[Open] Reports dir: {path}")

    def _init_autostart_state(self) -> None:
        try:
            enabled = self._autostart_enabled()
            self.sw_autostart.select() if enabled else self.sw_autostart.deselect()
        except Exception:
            pass

    def _on_autostart_toggle(self) -> None:
        if self.sw_autostart.get():
            self._autostart_on()
        else:
            self._autostart_off()

    def _autostart_on(self) -> None:
        try:
            # Prefer GUI exe if built; otherwise pythonw module
            exe = Path(sys.executable)
            # if frozen exe, use it; else pythonw -m src.workproof.app_ui
            args = ""
            if exe.name.lower().endswith(".exe") and "python" not in exe.name.lower():
                target = exe
            else:
                pythonw = exe.parent / "pythonw.exe"
                target = pythonw if pythonw.exists() else exe
                args = "-m src.workproof.app_ui"
            lnk = add_startup_shortcut("WorkProof", target, args=args)
            self._append(f"[Autostart] Enabled via shortcut: {lnk}")
        except Exception as e:
            self._append(f"[Autostart] Failed: {e}")

    def _autostart_off(self) -> None:
        try:
            remove_startup_shortcut("WorkProof")
            self._append("[Autostart] Disabled")
        except Exception as e:
            self._append(f"[Autostart] Remove failed: {e}")

    def _autostart_enabled(self) -> bool:
        import os
        startup = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        return (startup / "WorkProof.lnk").exists()

    def _append(self, text: str) -> None:
        self.txt.insert("end", text + "\n")
        self.txt.see("end")

    def _set_status(self, running: bool, paused: bool) -> None:
        if running and not paused:
            self.status_dot.configure(text_color="#18c964")  # green
            self.status_text.configure(text="Tracking (running)")
        elif running and paused:
            self.status_dot.configure(text_color="#f5a524")  # amber
            self.status_text.configure(text="Paused")
        else:
            self.status_dot.configure(text_color="#d9534f")  # red
            self.status_text.configure(text="Stopped")

    def _refresh_async(self) -> None:
        threading.Thread(target=self._refresh_loop, daemon=True).start()

    def _refresh_loop(self) -> None:
        while True:
            try:
                self._set_status(self.sup.is_running(), self.sup.is_paused())
                today = date.today()
                summary = generate_text_summary(today, self.cfg.sampling_interval_seconds, self.cfg.db_path, self.cfg.idle_threshold_seconds)
                self.txt.delete("1.0", "end")
                self.txt.insert("1.0", f"Today's Summary\n\n{summary}\n\nRecent Sessions\n")
                # list last few sessions (rebuilt from logs)
                from datetime import datetime, time, timezone
                start = datetime.combine(today, time.min).replace(tzinfo=timezone.utc)
                end = datetime.combine(today, time.max).replace(tzinfo=timezone.utc)
                sessions = build_sessions_for_day(self.cfg.db_path, start, end, self.cfg.sampling_interval_seconds, self.cfg.idle_threshold_seconds, self.cfg.session_gap_seconds)
                for s in sessions[-10:]:
                    dur = (s.end_time - s.start_time).total_seconds() if s.end_time else 0
                    self.txt.insert("end", f"- {s.start_time.isoformat()} → {s.end_time and s.end_time.isoformat()}  {int(dur//60)}m  {s.main_app}\n")
            except Exception as e:
                self.txt.insert("end", f"\n[Error updating summary: {e}]\n")
            time.sleep(5)


if __name__ == "__main__":
    app = WorkProofApp()
    app.mainloop()


