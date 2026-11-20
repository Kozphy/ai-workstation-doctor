"""Scan use-case: collect → store → evaluate → store findings → report."""

from __future__ import annotations

import logging
import platform
from dataclasses import dataclass
from pathlib import Path

from awd import __version__
from awd.domain.enums import SessionStatus
from awd.domain.models import Fact, Finding, ScanSession, new_session_id, utc_now
from awd.domain.protocols import Check, Collector, FactStore, ReportWriter, RuleEngine

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ScanOutcome:
    session: ScanSession
    facts: tuple[Fact, ...]
    findings: tuple[Finding, ...]
    report: str
    report_path: Path | None


class ScanService:
    """Orchestrates one diagnostic scan."""

    def __init__(
        self,
        fact_store: FactStore,
        collectors: tuple[Collector, ...],
        checks: tuple[Check, ...],
        rule_engine: RuleEngine,
        report_writer: ReportWriter,
    ) -> None:
        self._store = fact_store
        self._collectors = collectors
        self._checks = checks
        self._engine = rule_engine
        self._reports = report_writer

    def run(self, output: Path | None = None) -> ScanOutcome:
        session = ScanSession(
            id=new_session_id(),
            started_at=utc_now(),
            awd_version=__version__,
            status=SessionStatus.RUNNING,
            host_name=platform.node() or None,
        )
        self._store.create_session(session)
        logger.info("Scan started session=%s", session.id)

        try:
            facts = self._collect_all()
            self._store.save_facts(session.id, facts)

            fact_map = {fact.key: fact for fact in facts}
            results = self._engine.run(self._checks, fact_map)
            findings = tuple(result.finding for result in results)
            self._store.save_findings(session.id, findings)

            finished = ScanSession(
                id=session.id,
                started_at=session.started_at,
                finished_at=utc_now(),
                host_name=session.host_name,
                awd_version=session.awd_version,
                status=SessionStatus.COMPLETED,
            )
            self._store.finish_session(finished)

            report = self._reports.write(finished, findings, facts, destination=output)
            logger.info(
                "Scan completed session=%s findings=%s",
                finished.id,
                len(findings),
            )
            return ScanOutcome(
                session=finished,
                facts=facts,
                findings=findings,
                report=report,
                report_path=output,
            )
        except Exception:
            failed = ScanSession(
                id=session.id,
                started_at=session.started_at,
                finished_at=utc_now(),
                host_name=session.host_name,
                awd_version=session.awd_version,
                status=SessionStatus.FAILED,
            )
            self._store.finish_session(failed)
            logger.exception("Scan failed session=%s", session.id)
            raise

    def _collect_all(self) -> tuple[Fact, ...]:
        collected: list[Fact] = []
        for collector in self._collectors:
            logger.debug("Collecting from %s", collector.collector_id)
            collected.extend(collector.collect())
        return tuple(collected)
