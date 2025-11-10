Packaging
---------

Windows (.exe via PyInstaller):
1) Ensure venv active and dependencies installed
2) Run PowerShell script:
```powershell
.\build_win_exe.ps1
```
This generates `dist/workproof/workproof.exe`.

Linux:
- AppImage/Flatpak/Deb are documented approaches; for simplicity, ship as a Python app with a launcher.
- See `build_linux.sh` for a simple PyInstaller build.

PDF Export Dependencies:
- WeasyPrint: `pip install weasyprint` + OS dependencies (GTK, Pango)
- wkhtmltopdf: install system package and ensure it’s in PATH for pdfkit



