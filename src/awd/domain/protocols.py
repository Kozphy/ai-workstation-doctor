"""Ports (interfaces). Implementations live in infrastructure packages.

These Protocol shapes are the Rust migration surface: each maps 1:1 to a trait.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from awd.domain.models import CheckResult, Fact, Finding, ScanSession


@runtime_checkable
class Collector(Protocol):
    """Read-only probe that emits facts. Must be time-boxed by the caller."""

    @property
    def collector_id(self) -> str:
        """Stable ID, e.g. ``python.runtime``."""

    def collect(self) -> Sequence[Fact]:
        """Gather facts. Never mutate the host."""


@runtime_checkable
class Check(Protocol):
    """Evaluates facts into a finding. Declarative packs will wrap this later."""

    @property
    def check_id(self) -> str:
        """Stable public ID, e.g. ``python.version.min``."""

    @property
    def title(self) -> str:
        """Human-readable title for reports and docs."""

    @property
    def depends_on(self) -> Sequence[str]:
        """Check IDs that must PASS before this check runs."""

    def evaluate(self, facts: Mapping[str, Fact]) -> CheckResult:
        """Produce a finding from the fact map keyed by ``Fact.key``."""


@runtime_checkable
class FactStore(Protocol):
    """Persistence for sessions, facts, and findings."""

    def create_session(self, session: ScanSession) -> None: ...

    def finish_session(self, session: ScanSession) -> None: ...

    def save_facts(self, session_id: str, facts: Sequence[Fact]) -> None: ...

    def save_findings(self, session_id: str, findings: Sequence[Finding]) -> None: ...

    def get_session(self, session_id: str) -> ScanSession | None: ...

    def latest_session(self) -> ScanSession | None: ...

    def list_facts(self, session_id: str) -> Sequence[Fact]: ...

    def list_findings(self, session_id: str) -> Sequence[Finding]: ...


@runtime_checkable
class RuleEngine(Protocol):
    """Runs checks as a dependency DAG over a fact map."""

    def run(
        self,
        checks: Sequence[Check],
        facts: Mapping[str, Fact],
    ) -> Sequence[CheckResult]:
        """Evaluate checks; skip dependents when a dependency did not PASS."""


@runtime_checkable
class ReportWriter(Protocol):
    """Renders findings for a session to an artifact."""

    def write(
        self,
        session: ScanSession,
        findings: Sequence[Finding],
        facts: Sequence[Fact],
        destination: Path | None = None,
    ) -> str:
        """Return report body; optionally write to ``destination``."""
