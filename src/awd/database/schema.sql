-- AI Workstation Doctor fact store (v1)
-- Stable for Rust migration: same tables, same column names, ISO-8601 timestamps.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version    INTEGER PRIMARY KEY,
    applied_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS scan_sessions (
    id           TEXT PRIMARY KEY,
    started_at   TEXT NOT NULL,
    finished_at  TEXT,
    host_name    TEXT,
    awd_version  TEXT NOT NULL,
    status       TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed'))
);

CREATE TABLE IF NOT EXISTS facts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id     TEXT    NOT NULL REFERENCES scan_sessions(id) ON DELETE CASCADE,
    key            TEXT    NOT NULL,
    value_json     TEXT    NOT NULL,
    source         TEXT    NOT NULL,
    collected_at   TEXT    NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1,
    UNIQUE (session_id, key)
);

CREATE INDEX IF NOT EXISTS idx_facts_session ON facts(session_id);
CREATE INDEX IF NOT EXISTS idx_facts_key ON facts(key);

CREATE TABLE IF NOT EXISTS findings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    TEXT NOT NULL REFERENCES scan_sessions(id) ON DELETE CASCADE,
    check_id      TEXT NOT NULL,
    severity      TEXT NOT NULL,
    status        TEXT NOT NULL CHECK (status IN ('pass', 'fail', 'warn', 'skip', 'error')),
    title         TEXT NOT NULL,
    message       TEXT NOT NULL,
    evidence_json TEXT NOT NULL DEFAULT '[]',
    created_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_findings_session ON findings(session_id);
CREATE INDEX IF NOT EXISTS idx_findings_check ON findings(check_id);
