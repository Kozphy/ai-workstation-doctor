"""Composition root — wires adapters for the CLI.

Keep construction here so domain and use-cases stay free of concrete imports.
A Rust binary would replace this with its own wiring.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from awd.checks.ports import AnyPrimaryRunnerPortCheck, PortCatalogCheck
from awd.checks.python_version import PythonVersionCheck
from awd.checks.system import WindowsSystemProbeCheck
from awd.collectors.ports import LocalAiPortsCollector
from awd.collectors.python_runtime import PythonRuntimeCollector
from awd.collectors.windows_system import WindowsSystemCollector
from awd.database.connection import Database, default_db_path
from awd.database.fact_store import SqliteFactStore
from awd.domain.protocols import Check, Collector, FactStore, ReportWriter, RuleEngine
from awd.reports.markdown import MarkdownReportWriter
from awd.rules.engine import SimpleRuleEngine


@dataclass(slots=True)
class AppContainer:
    """Injectable dependencies for application services."""

    fact_store: FactStore
    collectors: tuple[Collector, ...]
    checks: tuple[Check, ...]
    rule_engine: RuleEngine
    report_writer: ReportWriter
    db_path: Path

    @classmethod
    def build(cls, db_path: Path | None = None) -> AppContainer:
        path = db_path or default_db_path()
        database = Database(path)
        store = SqliteFactStore(database)
        return cls(
            fact_store=store,
            collectors=(
                PythonRuntimeCollector(),
                WindowsSystemCollector(),
                LocalAiPortsCollector(),
            ),
            checks=(
                PythonVersionCheck(),
                WindowsSystemProbeCheck(),
                PortCatalogCheck(),
                AnyPrimaryRunnerPortCheck(),
            ),
            rule_engine=SimpleRuleEngine(),
            report_writer=MarkdownReportWriter(),
            db_path=path,
        )
