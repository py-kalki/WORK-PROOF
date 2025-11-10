Autostart (Windows & Linux)
---------------------------

Windows (Startup folder - recommended):
1) Create a shortcut in: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`
   Target: `workproof_gui.exe` (after building) or `pythonw.exe -m src.workproof.app_ui`
   Start in: your repo root

Windows (Registry Run key - alternative):
1) Run `regedit`
2) Navigate to `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
3) Add a new string value, e.g., `WorkProof` with the full path to `workproof_gui.exe`
Tradeoffs: Registry is less visible to users, Startup folder is easier to manage.

Linux (XDG autostart):
Create `~/.config/autostart/workproof.desktop`:
```
[Desktop Entry]
Type=Application
Name=WorkProof
Exec=python3 -m workproof.main
X-GNOME-Autostart-enabled=true
```



