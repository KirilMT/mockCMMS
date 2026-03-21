-- File Lock System Schema
-- Used by lock_manager.py (SQLite or PostgreSQL)

CREATE TABLE IF NOT EXISTS file_locks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path     TEXT    UNIQUE NOT NULL,
    developer_id  TEXT    NOT NULL,
    developer_email TEXT,
    lock_token    TEXT    UNIQUE NOT NULL,
    acquired_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at    DATETIME NOT NULL,
    released_at   DATETIME,
    branch_name   TEXT,
    reason        TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_file_path    ON file_locks(file_path);
CREATE INDEX IF NOT EXISTS idx_developer_id ON file_locks(developer_id);
CREATE INDEX IF NOT EXISTS idx_expires_at   ON file_locks(expires_at);
CREATE INDEX IF NOT EXISTS idx_released_at  ON file_locks(released_at);

-- Active locks view (not expired, not released)
CREATE VIEW IF NOT EXISTS active_locks AS
    SELECT * FROM file_locks
    WHERE released_at IS NULL
      AND expires_at > datetime('now');
