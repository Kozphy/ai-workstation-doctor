"""Unit tests for the sample Python runtime collector."""

from __future__ import annotations

import sys

from awd.collectors.python_runtime import PythonRuntimeCollector


def test_collects_expected_keys() -> None:
    facts = {f.key: f for f in PythonRuntimeCollector().collect()}
    assert "python.version" in facts
    assert "python.version_tuple" in facts
    assert "python.executable" in facts
    assert facts["python.executable"].value == sys.executable
    assert facts["python.version_tuple"].source == "python.runtime"


def test_version_tuple_matches_runtime() -> None:
    facts = {f.key: f for f in PythonRuntimeCollector().collect()}
    major, minor, patch = sys.version_info[:3]
    assert facts["python.version_tuple"].value == {
        "major": major,
        "minor": minor,
        "patch": patch,
    }
    assert facts["python.version"].value == f"{major}.{minor}.{patch}"
