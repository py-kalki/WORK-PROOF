from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Callable, Optional

try:
    import pystray  # type: ignore
    from PIL import Image  # type: ignore
except Exception:
    pystray = None  # type: ignore
    Image = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class TrayController:
    def __init__(self, icon_path: Path, on_pause: Callable[[], None], on_resume: Callable[[], None], on_quit: Callable[[], None], on_report: Callable[[], None]) -> None:
        self.icon_path = icon_path
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_quit = on_quit
        self.on_report = on_report
        self._thread: Optional[threading.Thread] = None
        self._icon = None

    def start(self) -> None:
        if not pystray or not Image:
            LOGGER.warning("pystray/PIL not installed; skipping tray")
            return
        image = Image.open(self.icon_path) if self.icon_path.exists() else Image.new("RGB", (64, 64), color=(50, 100, 200))
        menu = pystray.Menu(
            pystray.MenuItem("Pause", lambda: self.on_pause()),
            pystray.MenuItem("Resume", lambda: self.on_resume()),
            pystray.MenuItem("Generate Report", lambda: self.on_report()),
            pystray.MenuItem("Quit", lambda: self.on_quit()),
        )
        self._icon = pystray.Icon("WorkProof", image, "WorkProof", menu)
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        try:
            if self._icon:
                self._icon.stop()
        except Exception:
            pass



