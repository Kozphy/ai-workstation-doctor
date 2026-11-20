"""Unit tests for SimpleRuleEngine dependency handling."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from awd.domain.enums import FindingStatus, Severity
from awd.domain.models import CheckResult, Fact, Finding
from awd.rules.engine import SimpleRuleEngine


class _StubCheck:
    def __init__(
        self,
        check_id: str,
        status: FindingStatus,
        depends_on: Sequence[str] = (),
    ) -> None:
        self._check_id = check_id
        self._status = status
        self._depends_on = tuple(depends_on)

    @property
    def check_id(self) -> str:
        return self._check_id

    @property
    def title(self) -> str:
        return self._check_id

    @property
    def depends_on(self) -> Sequence[str]:
        return self._depends_on

    def evaluate(self, facts: Mapping[str, Fact]) -> CheckResult:
        return CheckResult(
            finding=Finding(
                check_id=self.check_id,
                title=self.title,
                status=self._status,
                severity=Severity.INFO,
                message="stub",
            )
        )


def test_skips_when_dependency_fails() -> None:
    engine = SimpleRuleEngine()
    results = engine.run(
        [
            _StubCheck("root", FindingStatus.FAIL),
            _StubCheck("child", FindingStatus.PASS, depends_on=("root",)),
        ],
        {},
    )
    by_id = {r.finding.check_id: r.finding.status for r in results}
    assert by_id["root"] == FindingStatus.FAIL
    assert by_id["child"] == FindingStatus.SKIP


def test_runs_when_dependency_passes() -> None:
    engine = SimpleRuleEngine()
    results = engine.run(
        [
            _StubCheck("root", FindingStatus.PASS),
            _StubCheck("child", FindingStatus.PASS, depends_on=("root",)),
        ],
        {},
    )
    by_id = {r.finding.check_id: r.finding.status for r in results}
    assert by_id["child"] == FindingStatus.PASS
