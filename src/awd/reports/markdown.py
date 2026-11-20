"""Markdown report renderer with shareable redaction."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from awd.domain.enums import FindingStatus
from awd.domain.models import Fact, Finding, ScanSession
from awd.reports.redact import RedactionProfile, redact_text

_STATUS_ICON = {
    FindingStatus.PASS: "OK",
    FindingStatus.FAIL: "FAIL",
    FindingStatus.WARN: "WARN",
    FindingStatus.SKIP: "SKIP",
    FindingStatus.ERROR: "ERROR",
}


class MarkdownReportWriter:
    """Renders a scan session as redacted, shareable Markdown."""

    def __init__(
        self,
        redaction: RedactionProfile | None = None,
        *,
        redact: bool = True,
    ) -> None:
        self._redaction = redaction
        self._redact = redact

    def write(
        self,
        session: ScanSession,
        findings: Sequence[Finding],
        facts: Sequence[Fact],
        destination: Path | None = None,
    ) -> str:
        body = self._render(session, findings, facts)
        if self._redact:
            body = redact_text(body, self._redaction)
        if destination is not None:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(body, encoding="utf-8")
        return body

    def _render(
        self,
        session: ScanSession,
        findings: Sequence[Finding],
        facts: Sequence[Fact],
    ) -> str:
        counts = {status: 0 for status in FindingStatus}
        for finding in findings:
            counts[finding.status] += 1

        lines: list[str] = [
            "# AI Workstation Doctor — Scan Report",
            "",
            f"- **Session:** `{session.id}`",
            f"- **Started:** {session.started_at.isoformat()}",
            f"- **Finished:** {session.finished_at.isoformat() if session.finished_at else 'n/a'}",
            f"- **Host:** {session.host_name or 'unknown'}",
            f"- **AWD version:** {session.awd_version}",
            f"- **Status:** {session.status.value}",
            "",
            "## Summary",
            "",
            "| Pass | Fail | Warn | Skip | Error |",
            "| ---: | ---: | ---: | ---: | ---: |",
            (
                f"| {counts[FindingStatus.PASS]} | {counts[FindingStatus.FAIL]} "
                f"| {counts[FindingStatus.WARN]} | {counts[FindingStatus.SKIP]} "
                f"| {counts[FindingStatus.ERROR]} |"
            ),
            "",
            "## Findings",
            "",
        ]

        if not findings:
            lines.append("_No findings._")
            lines.append("")
        else:
            for finding in findings:
                icon = _STATUS_ICON[finding.status]
                lines.append(f"### [{icon}] {finding.title}")
                lines.append("")
                lines.append(f"- **Check ID:** `{finding.check_id}`")
                lines.append(f"- **Status:** `{finding.status.value}`")
                lines.append(f"- **Severity:** `{finding.severity.value}`")
                lines.append(f"- **Message:** {finding.message}")
                if finding.evidence:
                    lines.append("- **Evidence:**")
                    for item in finding.evidence:
                        lines.append(f"  - `{item}`")
                lines.append("")

        lines.extend(["## Facts", ""])
        if not facts:
            lines.append("_No facts._")
            lines.append("")
        else:
            lines.append("| Key | Value | Source |")
            lines.append("| --- | --- | --- |")
            for fact in facts:
                value = repr(fact.value) if not isinstance(fact.value, str) else fact.value
                value = value.replace("|", "\\|").replace("\n", " ")
                lines.append(f"| `{fact.key}` | `{value}` | `{fact.source}` |")
            lines.append("")

        lines.append("---")
        lines.append(
            "_Generated locally by AI Workstation Doctor. "
            "Personal paths and host identity are redacted for sharing. "
            "Nothing was sent off-device._"
        )
        lines.append("")
        return "\n".join(lines)
