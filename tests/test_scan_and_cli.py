"""Integration-ish tests for scan service and CLI commands."""

from __future__ import annotations

from pathlib import Path

from awd.app.container import AppContainer
from awd.app.scan_service import ScanService
from awd.app.status_service import StatusService
from awd.cli.main import main
from awd.domain.enums import FindingStatus, SessionStatus


def test_scan_service_end_to_end(container: AppContainer, tmp_path: Path) -> None:
    report_path = tmp_path / "report.md"
    service = ScanService(
        fact_store=container.fact_store,
        collectors=container.collectors,
        checks=container.checks,
        rule_engine=container.rule_engine,
        report_writer=container.report_writer,
    )
    outcome = service.run(output=report_path)

    assert outcome.session.status == SessionStatus.COMPLETED
    assert outcome.facts
    assert any(f.key == "system.probe_status" for f in outcome.facts)
    assert any(f.key == "ports.results" for f in outcome.facts)
    by_id = {f.check_id: f for f in outcome.findings}
    assert by_id["python.version.min"].status == FindingStatus.PASS
    assert by_id["system.windows_probe"].status in {
        FindingStatus.PASS,
        FindingStatus.WARN,
    }
    assert by_id["ports.catalog"].status == FindingStatus.PASS
    assert by_id["ports.any_primary_runner"].status in {
        FindingStatus.PASS,
        FindingStatus.WARN,
    }
    assert report_path.is_file()
    text = report_path.read_text(encoding="utf-8")
    assert "AI Workstation Doctor" in text
    assert "python.version.min" in text
    assert "ports.any_primary_runner" in text

    snapshot = StatusService(container.fact_store).latest()
    assert snapshot.session is not None
    # WARN (no runners) does not make the machine "unhealthy" — only fail/error do.
    assert snapshot.fail_count == 0
    assert snapshot.error_count == 0
    assert snapshot.healthy is True


def test_cli_scan_status_report(tmp_path: Path) -> None:
    db = tmp_path / "cli.db"
    report = tmp_path / "out.md"

    assert main(["--db", str(db), "scan", "-o", str(report)]) == 0
    assert report.is_file()
    report_text = report.read_text(encoding="utf-8")
    assert "ports.catalog" in report_text
    assert main(["--db", str(db), "status"]) == 0
    assert main(["--db", str(db), "report", "-o", str(tmp_path / "again.md")]) == 0
