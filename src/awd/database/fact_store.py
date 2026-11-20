"""SQLite implementation of FactStore."""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from datetime import datetime

from awd.database.connection import Database
from awd.domain.enums import FindingStatus, SessionStatus, Severity
from awd.domain.models import Fact, Finding, ScanSession

logger = logging.getLogger(__name__)


def _dt_to_iso(value: datetime) -> str:
    return value.isoformat()


def _iso_to_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


class SqliteFactStore:
    """Persists sessions, facts, and findings in SQLite."""

    def __init__(self, database: Database) -> None:
        self._db = database
        self._db.initialize()

    def create_session(self, session: ScanSession) -> None:
        with self._db.connect() as conn:
            conn.execute(
                """
                INSERT INTO scan_sessions(id, started_at, finished_at, host_name, awd_version, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session.id,
                    _dt_to_iso(session.started_at),
                    _dt_to_iso(session.finished_at) if session.finished_at else None,
                    session.host_name,
                    session.awd_version,
                    session.status.value,
                ),
            )
            conn.commit()
        logger.debug("Created session %s", session.id)

    def finish_session(self, session: ScanSession) -> None:
        with self._db.connect() as conn:
            conn.execute(
                """
                UPDATE scan_sessions
                   SET finished_at = ?, status = ?, host_name = ?
                 WHERE id = ?
                """,
                (
                    _dt_to_iso(session.finished_at) if session.finished_at else None,
                    session.status.value,
                    session.host_name,
                    session.id,
                ),
            )
            conn.commit()

    def save_facts(self, session_id: str, facts: Sequence[Fact]) -> None:
        with self._db.connect() as conn:
            for fact in facts:
                conn.execute(
                    """
                    INSERT INTO facts(session_id, key, value_json, source, collected_at, schema_version)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id, key) DO UPDATE SET
                        value_json = excluded.value_json,
                        source = excluded.source,
                        collected_at = excluded.collected_at,
                        schema_version = excluded.schema_version
                    """,
                    (
                        session_id,
                        fact.key,
                        json.dumps(fact.value),
                        fact.source,
                        _dt_to_iso(fact.collected_at),
                        fact.schema_version,
                    ),
                )
            conn.commit()

    def save_findings(self, session_id: str, findings: Sequence[Finding]) -> None:
        with self._db.connect() as conn:
            for finding in findings:
                conn.execute(
                    """
                    INSERT INTO findings(
                        session_id, check_id, severity, status, title, message, evidence_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        finding.check_id,
                        finding.severity.value,
                        finding.status.value,
                        finding.title,
                        finding.message,
                        json.dumps(list(finding.evidence)),
                        _dt_to_iso(finding.created_at),
                    ),
                )
            conn.commit()

    def get_session(self, session_id: str) -> ScanSession | None:
        with self._db.connect() as conn:
            row = conn.execute(
                "SELECT * FROM scan_sessions WHERE id = ?", (session_id,)
            ).fetchone()
        return self._row_to_session(row) if row else None

    def latest_session(self) -> ScanSession | None:
        with self._db.connect() as conn:
            row = conn.execute(
                "SELECT * FROM scan_sessions ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
        return self._row_to_session(row) if row else None

    def list_facts(self, session_id: str) -> Sequence[Fact]:
        with self._db.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM facts WHERE session_id = ? ORDER BY key",
                (session_id,),
            ).fetchall()
        return tuple(
            Fact(
                key=row["key"],
                value=json.loads(row["value_json"]),
                source=row["source"],
                collected_at=_iso_to_dt(row["collected_at"]),
                schema_version=int(row["schema_version"]),
            )
            for row in rows
        )

    def list_findings(self, session_id: str) -> Sequence[Finding]:
        with self._db.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM findings WHERE session_id = ? ORDER BY id",
                (session_id,),
            ).fetchall()
        return tuple(
            Finding(
                check_id=row["check_id"],
                title=row["title"],
                status=FindingStatus(row["status"]),
                severity=Severity(row["severity"]),
                message=row["message"],
                evidence=tuple(json.loads(row["evidence_json"])),
                created_at=_iso_to_dt(row["created_at"]),
            )
            for row in rows
        )

    @staticmethod
    def _row_to_session(row: object) -> ScanSession:
        # sqlite3.Row supports mapping access
        r = row  # type: ignore[assignment]
        finished = r["finished_at"]  # type: ignore[index]
        return ScanSession(
            id=r["id"],  # type: ignore[index]
            started_at=_iso_to_dt(r["started_at"]),  # type: ignore[index]
            finished_at=_iso_to_dt(finished) if finished else None,
            host_name=r["host_name"],  # type: ignore[index]
            awd_version=r["awd_version"],  # type: ignore[index]
            status=SessionStatus(r["status"]),  # type: ignore[index]
        )
