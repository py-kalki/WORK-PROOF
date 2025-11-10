from __future__ import annotations

import json
import platform
import subprocess
from typing import Dict, List, Optional

try:
    import pygetwindow as gw  # type: ignore
except Exception:
    gw = None  # type: ignore

try:
    import win32gui  # type: ignore
    import win32process  # type: ignore
    import psutil  # type: ignore
except Exception:
    win32gui = None  # type: ignore
    win32process = None  # type: ignore
    import psutil  # type: ignore


def get_active_window_title() -> Optional[str]:
    system = platform.system()
    if system == "Windows":
        # Prefer pywin32 for accuracy; fallback to pygetwindow
        if win32gui:
            try:
                hwnd = win32gui.GetForegroundWindow()
                title = win32gui.GetWindowText(hwnd)
                return title or None
            except Exception:
                pass
        if gw:
            try:
                w = gw.getActiveWindow()
                if w:
                    return w.title or None
            except Exception:
                pass
        return None
    else:
        # Linux: try wmctrl, xprop (X11) best-effort; Wayland often restricted
        for cmd in (["wmctrl", "-lx"], ["xprop", "-root", "_NET_ACTIVE_WINDOW"],):
            try:
                out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True, timeout=1.5)
                if "wmctrl" in cmd[0]:
                    # crude parse last active entry
                    line = out.strip().splitlines()[-1:]
                    if line:
                        parts = line[0].split(None, 4)
                        if len(parts) >= 5:
                            return parts[4]
                else:
                    # xprop flow requires follow-up; skip for simplicity
                    continue
            except Exception:
                continue
        return None


def list_running_processes(limit: int = 40) -> List[str]:
    names: List[str] = []
    try:
        for p in psutil.process_iter(attrs=["name"]):
            name = p.info.get("name")
            if name:
                names.append(str(name))
            if len(names) >= limit:
                break
    except Exception:
        pass
    return names


def processes_json(limit: int = 40) -> str:
    return json.dumps(list_running_processes(limit=limit), ensure_ascii=False)



