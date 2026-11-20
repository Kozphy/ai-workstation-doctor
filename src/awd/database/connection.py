"""SQLite connection helpers and schema migration."""

from __future__ import annotations

import logging
import sqlite3
from importlib import resources
from pathlib import Path

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1


def default_db_path() -> Path:
    """User-local database path (Windows-friendly; works elsewhere for tests)."""
    root = Path.home() / ".awd"
    root.mkdir(parents=True, exist_ok=True)
    return root / "awd.db"


def _load_schema_sql() -> str:
    return resources.files("awd.database").joinpath("schema.sql").read_text(encoding="utf-8")


class Database:
    """Thin connection factory. Owns migration application."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self) -> None:
        """Apply schema if needed. Idempotent."""
        sql = _load_schema_sql()
        with self.connect() as conn:
            conn.executescript(sql)
            row = conn.execute(
                "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1"
            ).fetchone()
            current = int(row["version"]) if row else 0
            if current < SCHEMA_VERSION:
                from datetime import datetime, timezone

                now = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    "INSERT OR REPLACE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (SCHEMA_VERSION, now),
                )
                conn.commit()
                logger.info("Applied schema version %s to %s", SCHEMA_VERSION, self.path)
