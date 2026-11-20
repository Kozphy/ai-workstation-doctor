"""Domain models and ports (framework-agnostic)."""

from __future__ import annotations

from awd.domain.enums import FindingStatus, Severity
from awd.domain.models import CheckResult, Fact, Finding, ScanSession
from awd.domain.protocols import Check, Collector, FactStore, ReportWriter, RuleEngine

__all__ = [
    "Check",
    "CheckResult",
    "Collector",
    "Fact",
    "FactStore",
    "Finding",
    "FindingStatus",
    "ReportWriter",
    "RuleEngine",
    "ScanSession",
    "Severity",
]
