"""Foundation rule engine: topological evaluation with skip-on-failed-deps."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence

from awd.domain.enums import FindingStatus, Severity
from awd.domain.models import CheckResult, Fact, Finding
from awd.domain.protocols import Check

logger = logging.getLogger(__name__)


class SimpleRuleEngine:
    """Evaluates checks in dependency order.

    A check is SKIPPED when any dependency did not PASS.
    Cycles raise ``ValueError`` (fail fast during development).
    """

    def run(
        self,
        checks: Sequence[Check],
        facts: Mapping[str, Fact],
    ) -> Sequence[CheckResult]:
        by_id = {check.check_id: check for check in checks}
        if len(by_id) != len(checks):
            raise ValueError("Duplicate check_id in check list")

        order = self._topo_sort(by_id)
        outcomes: dict[str, FindingStatus] = {}
        results: list[CheckResult] = []

        for check_id in order:
            check = by_id[check_id]
            failed_deps = [
                dep
                for dep in check.depends_on
                if outcomes.get(dep, FindingStatus.ERROR) != FindingStatus.PASS
            ]
            if failed_deps:
                finding = Finding(
                    check_id=check.check_id,
                    title=check.title,
                    status=FindingStatus.SKIP,
                    severity=Severity.INFO,
                    message=f"Skipped because dependencies did not pass: {', '.join(failed_deps)}",
                    evidence=tuple(failed_deps),
                )
                result = CheckResult(finding=finding)
            else:
                logger.debug("Evaluating check %s", check_id)
                result = check.evaluate(facts)

            outcomes[check_id] = result.finding.status
            results.append(result)

        return tuple(results)

    @staticmethod
    def _topo_sort(by_id: Mapping[str, Check]) -> list[str]:
        visiting: set[str] = set()
        visited: set[str] = set()
        order: list[str] = []

        def visit(node: str) -> None:
            if node in visited:
                return
            if node in visiting:
                raise ValueError(f"Cycle detected involving check '{node}'")
            if node not in by_id:
                raise ValueError(f"Unknown dependency check_id '{node}'")
            visiting.add(node)
            for dep in by_id[node].depends_on:
                visit(dep)
            visiting.remove(node)
            visited.add(node)
            order.append(node)

        for check_id in by_id:
            visit(check_id)
        return order
