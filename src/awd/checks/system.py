"""Health check for the optional Windows hardware probe."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from awd.domain.enums import FindingStatus, Severity
from awd.domain.models import CheckResult, Fact, Finding


class WindowsSystemProbeCheck:
    """Report whether the read-only Windows hardware probe completed."""

    @property
    def check_id(self) -> str:
        return "system.windows_probe"

    @property
    def title(self) -> str:
        return "Windows hardware information is available"

    @property
    def depends_on(self) -> Sequence[str]:
        return ()

    def evaluate(self, facts: Mapping[str, Fact]) -> CheckResult:
        status = facts.get("system.probe_status")
        if status is None:
            return CheckResult(
                finding=Finding(
                    check_id=self.check_id,
                    title=self.title,
                    status=FindingStatus.ERROR,
                    severity=Severity.MEDIUM,
                    message="Missing system.probe_status fact.",
                )
            )

        if status.value == "ok":
            return CheckResult(
                finding=Finding(
                    check_id=self.check_id,
                    title=self.title,
                    status=FindingStatus.PASS,
                    severity=Severity.INFO,
                    message="Windows hardware facts were collected.",
                )
            )

        error = facts.get("system.probe_error")
        detail = f" Evidence: {error.value}" if error is not None else ""
        if status.value == "unsupported":
            message = f"Windows hardware probe is not applicable on this platform.{detail}"
        else:
            message = f"Windows hardware facts could not be collected.{detail}"
        return CheckResult(
            finding=Finding(
                check_id=self.check_id,
                title=self.title,
                status=FindingStatus.WARN,
                severity=Severity.LOW,
                message=message,
                evidence=(f"system.probe_status={status.value}",),
            )
        )
