"""Status use-case: summarize latest scan without re-probing."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from awd.domain.enums import FindingStatus
from awd.domain.models import Finding, ScanSession
from awd.domain.protocols import FactStore


@dataclass(frozen=True, slots=True)
class StatusSnapshot:
    session: ScanSession | None
    findings: tuple[Finding, ...]
    pass_count: int
    fail_count: int
    warn_count: int
    skip_count: int
    error_count: int

    @property
    def healthy(self) -> bool:
        return self.session is not None and self.fail_count == 0 and self.error_count == 0


class StatusService:
    def __init__(self, fact_store: FactStore) -> None:
        self._store = fact_store

    def latest(self) -> StatusSnapshot:
        session = self._store.latest_session()
        if session is None:
            return StatusSnapshot(
                session=None,
                findings=(),
                pass_count=0,
                fail_count=0,
                warn_count=0,
                skip_count=0,
                error_count=0,
            )
        findings = tuple(self._store.list_findings(session.id))
        return StatusSnapshot(
            session=session,
            findings=findings,
            pass_count=_count(findings, FindingStatus.PASS),
            fail_count=_count(findings, FindingStatus.FAIL),
            warn_count=_count(findings, FindingStatus.WARN),
            skip_count=_count(findings, FindingStatus.SKIP),
            error_count=_count(findings, FindingStatus.ERROR),
        )


def _count(findings: Sequence[Finding], status: FindingStatus) -> int:
    return sum(1 for finding in findings if finding.status == status)
