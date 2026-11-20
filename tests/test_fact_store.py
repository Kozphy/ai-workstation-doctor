"""Unit tests for SqliteFactStore."""

from __future__ import annotations

from awd import __version__
from awd.database.fact_store import SqliteFactStore
from awd.domain.enums import FindingStatus, SessionStatus, Severity
from awd.domain.models import Fact, Finding, ScanSession, new_session_id, utc_now


def test_round_trip_session_facts_findings(fact_store: SqliteFactStore) -> None:
    session = ScanSession(
        id=new_session_id(),
        started_at=utc_now(),
        awd_version=__version__,
        status=SessionStatus.RUNNING,
        host_name="test-host",
    )
    fact_store.create_session(session)

    facts = (
        Fact(key="python.version", value="3.12.0", source="test"),
        Fact(key="os.system", value="Windows", source="test"),
    )
    fact_store.save_facts(session.id, facts)

    finding = Finding(
        check_id="python.version.min",
        title="Python 3.12 or newer",
        status=FindingStatus.PASS,
        severity=Severity.INFO,
        message="ok",
        evidence=("python.version=3.12.0",),
    )
    fact_store.save_findings(session.id, (finding,))

    finished = ScanSession(
        id=session.id,
        started_at=session.started_at,
        finished_at=utc_now(),
        host_name=session.host_name,
        awd_version=session.awd_version,
        status=SessionStatus.COMPLETED,
    )
    fact_store.finish_session(finished)

    loaded = fact_store.get_session(session.id)
    assert loaded is not None
    assert loaded.status == SessionStatus.COMPLETED
    assert loaded.host_name == "test-host"

    assert fact_store.latest_session() is not None
    assert len(fact_store.list_facts(session.id)) == 2
    stored_findings = fact_store.list_findings(session.id)
    assert len(stored_findings) == 1
    assert stored_findings[0].check_id == "python.version.min"
    assert stored_findings[0].evidence == ("python.version=3.12.0",)
