"""``awd`` command-line entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from awd import __version__
from awd.app.container import AppContainer
from awd.app.scan_service import ScanService
from awd.app.status_service import StatusService
from awd.logging_config import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="awd",
        description="AI Workstation Doctor — local AI diagnostics for Windows",
    )
    parser.add_argument("--version", action="version", version=f"awd {__version__}")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase log verbosity (-v INFO, -vv DEBUG)",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="SQLite database path (default: ~/.awd/awd.db)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Collect facts, run checks, store results")
    scan.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write Markdown report to this path",
    )

    report = sub.add_parser("report", help="Render Markdown for the latest scan")
    report.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write Markdown report to this path (default: stdout)",
    )

    sub.add_parser("status", help="Show latest scan summary")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.verbose)

    container = AppContainer.build(db_path=args.db)

    if args.command == "scan":
        return _cmd_scan(container, args.output)
    if args.command == "report":
        return _cmd_report(container, args.output)
    if args.command == "status":
        return _cmd_status(container)
    parser.error(f"Unknown command: {args.command}")
    return 2


def _cmd_scan(container: AppContainer, output: Path | None) -> int:
    service = ScanService(
        fact_store=container.fact_store,
        collectors=container.collectors,
        checks=container.checks,
        rule_engine=container.rule_engine,
        report_writer=container.report_writer,
    )
    outcome = service.run(output=output)
    failed = sum(1 for f in outcome.findings if f.status.value in {"fail", "error"})
    print(f"Scan {outcome.session.id} completed ({len(outcome.findings)} findings).")
    print(f"Database: {container.db_path}")
    if outcome.report_path:
        print(f"Report written: {outcome.report_path}")
    else:
        print()
        print(outcome.report)
    return 1 if failed else 0


def _cmd_report(container: AppContainer, output: Path | None) -> int:
    session = container.fact_store.latest_session()
    if session is None:
        print("No scans yet. Run: awd scan", file=sys.stderr)
        return 1
    findings = container.fact_store.list_findings(session.id)
    facts = container.fact_store.list_facts(session.id)
    body = container.report_writer.write(session, findings, facts, destination=output)
    if output is None:
        print(body)
    else:
        print(f"Report written: {output}")
    return 0


def _cmd_status(container: AppContainer) -> int:
    snapshot = StatusService(container.fact_store).latest()
    if snapshot.session is None:
        print("No scans yet. Run: awd scan")
        return 0

    session = snapshot.session
    print(f"Session:  {session.id}")
    print(f"Status:   {session.status.value}")
    print(f"Started:  {session.started_at.isoformat()}")
    print(f"Finished: {session.finished_at.isoformat() if session.finished_at else 'n/a'}")
    print(f"Host:     {session.host_name or 'unknown'}")
    print(
        "Findings: "
        f"pass={snapshot.pass_count} fail={snapshot.fail_count} "
        f"warn={snapshot.warn_count} skip={snapshot.skip_count} error={snapshot.error_count}"
    )
    print(f"Healthy:  {'yes' if snapshot.healthy else 'no'}")
    print(f"Database: {container.db_path}")
    return 0 if snapshot.healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
