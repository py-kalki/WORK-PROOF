Project documentation index
===========================

This file is a convenient index that points to the project's existing documentation and explains where to find developer, packaging and usage guides.

Where to look
-------------

- `docs/installation.md` — long-form installation instructions and notes (also see `INSTALLATION.md` at repo root).
- `docs/autostart.md` — autostart/setup instructions for Windows & Linux.
- `docs/packaging.md` — packaging recommendations and distribution notes.
- `docs/privacy.md` — privacy and data retention policy.
- `docs/usage.md` — CLI and report generation usage examples.

Developer guide
---------------

- Source layout: `src/workproof/` contains the application package.
  - `main.py` — application entrypoint (foreground runner)
  - `tracker.py`, `file_watcher.py`, `report_generator.py`, etc.

- To run locally during development:

  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -e .
  pytest -q
  ```

- Useful scripts and locations:
  - `run_smoke_test.py` — quick verification run
  - `examples/` — scripts that show common operations (generate reports, import data)
  - `build_win_exe.ps1`, `build_linux.sh` — packaging helpers

Reports and templates
---------------------

- Report templates reside in `assets/templates/` (Jinja2 templates used by the report generator).
- Charts are generated with Matplotlib/Seaborn and embedded into the HTML reports.

Testing and CI
--------------

- Tests are under `tests/`. Run `pytest -q` to execute unit and integration tests.
- If you add dependencies modify `requirements.txt` and ensure tests pass locally.

Extending the project
---------------------

If you want to add new data collectors, follow these steps:

1. Add a new module under `src/workproof/`, keeping concerns separated (capture vs storage vs summarizer).
2. Add unit tests to `tests/` covering logic and edge cases.
3. Update `docs/usage.md` and `assets/templates/` if the data affects report content.

Contact and contribution
------------------------

Open issues or PRs on GitHub. Include a short description, steps to reproduce, and tests when appropriate.
