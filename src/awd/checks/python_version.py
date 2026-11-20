"""Sample check: require Python 3.12+."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from awd.domain.enums import FindingStatus, Severity
from awd.domain.models import CheckResult, Fact, Finding


class PythonVersionCheck:
    """Fails when the interpreter is older than the project baseline."""

    MIN_MAJOR = 3
    MIN_MINOR = 12

    @property
    def check_id(self) -> str:
        return "python.version.min"

    @property
    def title(self) -> str:
        return "Python 3.12 or newer"

    @property
    def depends_on(self) -> Sequence[str]:
        return ()

    def evaluate(self, facts: Mapping[str, Fact]) -> CheckResult:
        version_fact = facts.get("python.version_tuple")
        if version_fact is None:
            finding = Finding(
                check_id=self.check_id,
                title=self.title,
                status=FindingStatus.ERROR,
                severity=Severity.HIGH,
                message="Missing fact python.version_tuple — run collectors first.",
            )
            return CheckResult(finding=finding)

        value = version_fact.value
        if not isinstance(value, dict):
            finding = Finding(
                check_id=self.check_id,
                title=self.title,
                status=FindingStatus.ERROR,
                severity=Severity.HIGH,
                message=f"Unexpected python.version_tuple shape: {type(value).__name__}",
            )
            return CheckResult(finding=finding)

        major = int(value["major"])
        minor = int(value["minor"])
        patch = int(value.get("patch", 0))
        label = f"{major}.{minor}.{patch}"
        ok = (major, minor) >= (self.MIN_MAJOR, self.MIN_MINOR)

        finding = Finding(
            check_id=self.check_id,
            title=self.title,
            status=FindingStatus.PASS if ok else FindingStatus.FAIL,
            severity=Severity.INFO if ok else Severity.HIGH,
            message=(
                f"Python {label} meets the {self.MIN_MAJOR}.{self.MIN_MINOR}+ requirement."
                if ok
                else f"Python {label} is below the required {self.MIN_MAJOR}.{self.MIN_MINOR}."
            ),
            evidence=(
                f"python.version={label}",
                f"executable={_fact_value(facts, 'python.executable')}",
            ),
        )
        return CheckResult(finding=finding)


def _fact_value(facts: Mapping[str, Fact], key: str) -> str:
    fact = facts.get(key)
    return str(fact.value) if fact is not None else "<missing>"

