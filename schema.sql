CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    active_app TEXT,
    running_apps TEXT NOT NULL,
    idle_seconds INTEGER NOT NULL,
    project_path TEXT,
    event_type TEXT NOT NULL,
    meta TEXT
);

CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_logs_event_type ON logs(event_type);


