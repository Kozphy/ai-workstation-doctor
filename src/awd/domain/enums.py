"""Shared enumerations — keep string values stable for Rust migration."""

from __future__ import annotations

from enum import StrEnum


class Severity(StrEnum):
    """Finding severity. Values are public check-pack contracts."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingStatus(StrEnum):
    """Outcome of a single check evaluation."""

    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"
    ERROR = "error"


class SessionStatus(StrEnum):
    """Lifecycle of a scan session persisted in SQLite."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
