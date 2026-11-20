"""Fact collectors (read-only probes)."""

from __future__ import annotations

from awd.collectors.ports import LocalAiPortsCollector
from awd.collectors.python_runtime import PythonRuntimeCollector
from awd.collectors.windows_system import WindowsSystemCollector

__all__ = [
    "LocalAiPortsCollector",
    "PythonRuntimeCollector",
    "WindowsSystemCollector",
]
