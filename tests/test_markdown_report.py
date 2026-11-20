"""Tests for MarkdownReportWriter redaction integration."""

from __future__ import annotations

from pathlib import Path

from awd import __version__
from awd.domain.enums import FindingStatus, SessionStatus, Severity
from awd.domain.models import Fact, Finding, ScanSession, utc_now
from awd.reports.markdown import MarkdownReportWriter
from awd.reports.redact import RedactionProfile


def _sample_session(host: str = "SECRET-HOST") -> ScanSession:
    return ScanSession(
        id="11111111-1111-1111-1111-111111111111",
        started_at=utc_now(),
        finished_at=utc_now(),
        host_name=host,
        awd_version=__version__,
        status=SessionStatus.COMPLETED,
    )


def test_report_redacts_host_and_paths(tmp_path: Path) -> None:
    profile = RedactionProfile(
        username="carol",
        user_profile=r"C:\Users\carol",
        home=r"C:\Users\carol",
        host_name="SECRET-HOST",
    )
    writer = MarkdownReportWriter(redaction=profile)
    findings = (
        Finding(
            check_id="demo.check",
            title="Demo",
            status=FindingStatus.PASS,
            severity=Severity.INFO,
            message=r"OK for carol on SECRET-HOST",
            evidence=(r"executable=C:\Users\carol\Python\python.exe",),
        ),
    )
    facts = (
        Fact(
            key="python.executable",
            value=r"C:\Users\carol\Python\python.exe",
            source="test",
        ),
    )
    destination = tmp_path / "report.md"
    body = writer.write(_sample_session(), findings, facts, destination=destination)

    assert destination.is_file()
    assert "carol" not in body
    assert "SECRET-HOST" not in body
    assert "<host>" in body
    assert "<userprofile>" in body
    assert "redacted for sharing" in body
    assert "Nothing was sent off-device" in body


def test_redaction_can_be_disabled() -> None:
    writer = MarkdownReportWriter(
        redaction=RedactionProfile(username="dave", host_name="DAVE-PC"),
        redact=False,
    )
    findings = (
        Finding(
            check_id="demo.check",
            title="Demo",
            status=FindingStatus.PASS,
            severity=Severity.INFO,
            message="user dave on DAVE-PC",
        ),
    )
    body = writer.write(_sample_session("DAVE-PC"), findings, ())
    assert "dave" in body
    assert "DAVE-PC" in body
