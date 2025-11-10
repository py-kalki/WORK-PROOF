CLI Usage
---------

Run the tracker (foreground):
```bash
python -m workproof.main
```

Generate a report:
```bash
python -m workproof.report_generator --date 2025-01-01 --out reports/2025-01-01.html --pdf reports/2025-01-01.pdf
```

Purge old data (example keep=0 days):
```bash
python -c "from workproof.config import default_config; from workproof.database import purge_older_than; cfg=default_config(); print('Purged', purge_older_than(cfg.db_path, 0))"
```


