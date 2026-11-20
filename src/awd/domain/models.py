"""Immutable domain records. JSON-friendly for SQLite and a future Rust core."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from awd.domain.enums import FindingStatus, SessionStatus, Severity


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_session_id() -> str:
    return str(uuid4())


@dataclass(frozen=True, slots=True)
class Fact:
    """A typed observation from a collector.

    ``key`` is a stable dotted path (e.g. ``python.version``).
    ``value`` must be JSON-serializable.
    """

    key: str
    value: Any
    source: str
    collected_at: datetime = field(default_factory=utc_now)
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class Finding:
    """A check outcome with evidence for reports and repair planning."""

    check_id: str
    title: str
    status: FindingStatus
    severity: Severity
    message: str
    evidence: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True, slots=True)
class CheckResult:
    """Result returned by a Check implementation."""

    finding: Finding
    produced_facts: tuple[Fact, ...] = ()


@dataclass(frozen=True, slots=True)
class ScanSession:
    """One diagnostic run. Facts and findings hang off ``id``."""

    id: str
    started_at: datetime
    awd_version: str
    status: SessionStatus
    host_name: str | None = None
    finished_at: datetime | None = None
