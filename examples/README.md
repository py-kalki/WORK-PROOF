Examples
--------

- `load_sample_data.py`: Insert a small set of sample logs into your local DB.
- `generate_today_report.py`: Generate HTML (and try PDF) for today.

Quick demo:
```bash
python examples/load_sample_data.py
python examples/generate_today_report.py
```

Scheduling:
- Windows Task Scheduler: run `python -m workproof.report_generator --date today --out %USERPROFILE%\\WorkProof\\report.html`
- systemd user unit:
```
[Unit]
Description=WorkProof Tracker

[Service]
ExecStart=python3 -m workproof.main
Restart=on-failure

[Install]
WantedBy=default.target
```


