"""Shared pytest fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from awd.app.container import AppContainer
from awd.database.connection import Database
from awd.database.fact_store import SqliteFactStore
from awd.collectors.ports import LocalAiPortsCollector
from awd.collectors.python_runtime import PythonRuntimeCollector
from awd.collectors.windows_system import WindowsSystemCollector


@pytest.fixture
def container_factory():
    def build(db_path: Path | None = None) -> AppContainer:
        container = AppContainer.build(db_path=db_path)
        container.collectors = (
            PythonRuntimeCollector(),
            WindowsSystemCollector(platform_name="Linux"),
            LocalAiPortsCollector(probe=lambda _host, _port, _timeout: False),
        )
        return container

    return build

# Allow legacy ``import llama_autostart`` from the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test-awd.db"


@pytest.fixture
def fact_store(db_path: Path) -> SqliteFactStore:
    return SqliteFactStore(Database(db_path))


@pytest.fixture
def container(db_path: Path, container_factory) -> AppContainer:
    return container_factory(db_path)
