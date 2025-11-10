Installation
============

This document provides step-by-step installation instructions for WorkProof on Windows and Linux. It covers creating a virtual environment, installing dependencies, a quick smoke-test, and notes on packaging for distribution.

Prerequisites
-------------

- Python 3.9 or newer
- Git (optional, to clone the repo)
- On Windows: PowerShell (this repository's scripts assume PowerShell usage)
- On Linux: Bash and common build tools if you plan to package

Quick install (developer / local use)
-----------------------------------

1. Clone the repository (if needed):

   ```powershell
   git clone <repo-url>
   cd <repo-dir>
   ```

2. Create and activate a virtualenv (PowerShell example):

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install the package locally and dependencies:

   ```powershell
   pip install -e .
   pip install -r requirements.txt
   ```

   Note: `pip install -e .` makes the package importable (package metadata is in `pyproject.toml`).

4. Run the smoke test to verify basic functionality (short run):

   ```powershell
   python run_smoke_test.py
   ```

5. Start the tracker (foreground):

   ```powershell
   python -m workproof.main
   ```

Packaging / Distribution
------------------------

The repository contains helper scripts and PyInstaller specs for building distributables.

- Windows: use `build_win_exe.ps1`. This wraps a PyInstaller build using the provided `.spec` files.
  - Open PowerShell with appropriate execution policy.
  - Run: `.uild_win_exe.ps1` (inspect the script for arguments and output paths).

- Linux: `build_linux.sh` demonstrates how to build a package; you can adapt it for AppImage/Flatpak.

Notes on dependencies and packaging
----------------------------------

- Some packages have platform-specific dependencies (for example `pygetwindow`, `pywin32` on Windows).
- PDF generation has multiple options in this repo (WeasyPrint, pdfkit); packaging may require system libraries (libpango, GTK) for WeasyPrint.

Environment variables
---------------------

- WORKPROOF_BACKUP_PW: (optional) password used for scheduled encrypted backups when you enable the weekly backup job.

Troubleshooting
---------------

- If modules cannot be imported when running with `python -m workproof.main`, ensure you installed the package (`pip install -e .`) or set `PYTHONPATH` to include `./src`.
- On Windows, if PowerShell prevents script execution, you may need to run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` (or run activation commands from the prompt). Use caution and follow your org security policies.

What's next
-----------

See `DOCUMENTATION.md` (in repo root) and the `docs/` folder for detailed usage, packaging, autostart and privacy information.
