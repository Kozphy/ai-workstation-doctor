"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from awd.app.container import AppContainer
from awd.database.connection import Database
from awd.database.fact_store import SqliteFactStore


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test-awd.db"


@pytest.fixture
def fact_store(db_path: Path) -> SqliteFactStore:
    return SqliteFactStore(Database(db_path))


@pytest.fixture
def container(db_path: Path) -> AppContainer:
    return AppContainer.build(db_path=db_path)
