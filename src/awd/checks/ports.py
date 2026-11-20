"""Checks for the local AI port checker."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from awd.collectors.ports import LOCAL_AI_PORTS
from awd.domain.enums import FindingStatus, Severity
from awd.domain.models import CheckResult, Fact, Finding


class AnyPrimaryRunnerPortCheck:
    """Warn when none of the primary runner ports are listening.

    Primary ports: llama.cpp (9931), Ollama (11434), LM Studio (1234).
    Closed optional ports (OpenWebUI, vLLM, …) are not failures.
    """

    @property
    def check_id(self) -> str:
        return "ports.any_primary_runner"

    @property
    def title(self) -> str:
        return "At least one primary local AI runner port is open"

    @property
    def depends_on(self) -> Sequence[str]:
        return ()

    def evaluate(self, facts: Mapping[str, Fact]) -> CheckResult:
        flag = facts.get("ports.primary_any_open")
        results = facts.get("ports.results")
        if flag is None or results is None:
            return CheckResult(
                finding=Finding(
                    check_id=self.check_id,
                    title=self.title,
                    status=FindingStatus.ERROR,
                    severity=Severity.HIGH,
                    message="Missing port facts — ensure LocalAiPortsCollector ran.",
                )
            )

        evidence = _evidence_lines(results.value if isinstance(results.value, list) else [])
        if bool(flag.value):
            open_primary = facts.get("ports.primary_open")
            open_list = open_primary.value if open_primary is not None else []
            return CheckResult(
                finding=Finding(
                    check_id=self.check_id,
                    title=self.title,
                    status=FindingStatus.PASS,
                    severity=Severity.INFO,
                    message=f"Primary runner port(s) open: {open_list}",
                    evidence=evidence,
                )
            )

        primary_names = ", ".join(
            f"{p.name}:{p.port}" for p in LOCAL_AI_PORTS if p.primary_runner
        )
        return CheckResult(
            finding=Finding(
                check_id=self.check_id,
                title=self.title,
                status=FindingStatus.WARN,
                severity=Severity.MEDIUM,
                message=(
                    "No primary local AI runner port is open "
                    f"({primary_names}). Start Ollama, LM Studio, or llama.cpp, "
                    "or ignore if you are not running a local model server."
                ),
                evidence=evidence,
            )
        )


class PortCatalogCheck:
    """Always records a pass/info summary of every catalogued port."""

    @property
    def check_id(self) -> str:
        return "ports.catalog"

    @property
    def title(self) -> str:
        return "Local AI port catalog"

    @property
    def depends_on(self) -> Sequence[str]:
        return ()

    def evaluate(self, facts: Mapping[str, Fact]) -> CheckResult:
        results_fact = facts.get("ports.results")
        if results_fact is None or not isinstance(results_fact.value, list):
            return CheckResult(
                finding=Finding(
                    check_id=self.check_id,
                    title=self.title,
                    status=FindingStatus.ERROR,
                    severity=Severity.HIGH,
                    message="Missing ports.results fact.",
                )
            )

        rows = results_fact.value
        open_count = sum(1 for row in rows if isinstance(row, dict) and row.get("open"))
        evidence = _evidence_lines(rows)
        return CheckResult(
            finding=Finding(
                check_id=self.check_id,
                title=self.title,
                status=FindingStatus.PASS,
                severity=Severity.INFO,
                message=f"{open_count}/{len(rows)} catalogued local-AI ports are open on 127.0.0.1.",
                evidence=evidence,
            )
        )


def _evidence_lines(rows: list[object]) -> tuple[str, ...]:
    lines: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        port = row.get("port")
        name = row.get("name")
        state = "open" if row.get("open") else "closed"
        lines.append(f"{name}:{port}={state}")
    return tuple(lines)
