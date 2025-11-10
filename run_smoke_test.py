from __future__ import annotations

import time
from datetime import datetime, date

from src.workproof.config import default_config
from src.workproof.database import initialize, fetch_logs_between
from src.workproof.tracker import Tracker
from src.workproof.utils.logging_setup import setup_logging


def main() -> None:
    cfg = default_config({"sampling_interval_seconds": 5})
    setup_logging(cfg.logs_dir)
    initialize(cfg.db_path)
    tracker = Tracker(cfg, cfg.db_path)
    tracker.start()
    print("Smoke test running for ~60 seconds...")
    time.sleep(60)
    tracker.stop()
    tracker.join(timeout=2)
    # Print summary for today
    start = datetime.combine(date.today(), datetime.min.time()).astimezone().astimezone()
    end = datetime.combine(date.today(), datetime.max.time()).astimezone().astimezone()
    logs = list(fetch_logs_between(cfg.db_path, start, end))
    print(f"Collected {len(logs)} log rows today.")


if __name__ == "__main__":
    main()



