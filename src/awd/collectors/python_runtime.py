"""Sample collector: Python interpreter facts.

Foundation sample — proves the collector → fact-store path without WMI.
"""

from __future__ import annotations

import platform
import sys
from collections.abc import Sequence

from awd.domain.models import Fact


class PythonRuntimeCollector:
    """Collects interpreter version and platform identity."""

    @property
    def collector_id(self) -> str:
        return "python.runtime"

    def collect(self) -> Sequence[Fact]:
        source = self.collector_id
        major, minor, patch = sys.version_info[:3]
        return (
            Fact(key="python.version", value=f"{major}.{minor}.{patch}", source=source),
            Fact(
                key="python.version_tuple",
                value={"major": major, "minor": minor, "patch": patch},
                source=source,
            ),
            Fact(key="python.executable", value=sys.executable, source=source),
            Fact(key="python.implementation", value=platform.python_implementation(), source=source),
            Fact(key="os.system", value=platform.system(), source=source),
            Fact(key="os.release", value=platform.release(), source=source),
            Fact(key="os.machine", value=platform.machine(), source=source),
        )
