Privacy & Data Handling
-----------------------

What is collected:
- Timestamped samples: active window title, running process names (list), idle seconds
- File events within your configured Projects directory: path and event type

What is NOT collected:
- Keystrokes, screenshots, clipboard contents
- Network activity, credentials
- Anything outside the Projects directory for file events

Storage:
- Local SQLite at the path defined in `config.py` (default under your user data directory)
- WAL journaling enabled; retention policy configurable (default 60 days)

Purge:
```bash
python -c "from workproof.config import default_config; from workproof.database import purge_older_than; purge_older_than(default_config().db_path, 0)"
```

Sharing:
- Reports are generated locally. If you choose to share/export, confirm content.
- For client-facing exports, consider redacting sensitive filenames.



