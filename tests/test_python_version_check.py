"""Unit tests for the sample Python version check."""

from __future__ import annotations

from awd.checks.python_version import PythonVersionCheck
from awd.domain.enums import FindingStatus
from awd.domain.models import Fact


def _facts(major: int, minor: int, patch: int = 0) -> dict[str, Fact]:
    return {
        "python.version_tuple": Fact(
            key="python.version_tuple",
            value={"major": major, "minor": minor, "patch": patch},
            source="test",
        ),
        "python.executable": Fact(
            key="python.executable",
            value="/usr/bin/python",
            source="test",
        ),
    }


def test_passes_on_312() -> None:
    result = PythonVersionCheck().evaluate(_facts(3, 12, 0))
    assert result.finding.status == FindingStatus.PASS


def test_fails_on_311() -> None:
    result = PythonVersionCheck().evaluate(_facts(3, 11, 9))
    assert result.finding.status == FindingStatus.FAIL
    assert result.finding.check_id == "python.version.min"


def test_errors_when_fact_missing() -> None:
    result = PythonVersionCheck().evaluate({})
    assert result.finding.status == FindingStatus.ERROR
