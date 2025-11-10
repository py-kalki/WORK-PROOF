from __future__ import annotations

import os
from pathlib import Path
import win32com.client  # type: ignore
import winreg  # type: ignore


def add_startup_shortcut(app_name: str, target: Path, args: str = "") -> Path:
    startup = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    startup.mkdir(parents=True, exist_ok=True)
    lnk = startup / f"{app_name}.lnk"
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(str(lnk))
    shortcut.Targetpath = str(target)
    if args:
        shortcut.Arguments = args
    shortcut.WorkingDirectory = str(target.parent)
    shortcut.IconLocation = str(target)
    shortcut.save()
    return lnk


def remove_startup_shortcut(app_name: str) -> None:
    startup = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    lnk = startup / f"{app_name}.lnk"
    if lnk.exists():
        lnk.unlink()


def add_registry_run(app_name: str, command: str) -> None:
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
    winreg.CloseKey(key)


def remove_registry_run(app_name: str) -> None:
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
    try:
        winreg.DeleteValue(key, app_name)
    finally:
        winreg.CloseKey(key)


