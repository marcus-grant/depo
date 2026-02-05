# tests/fixtures/__init__.py
"""
Centralized test fixtures.

Prefix: t_ for first-party test fixtures.

Author: Marcus Grant
Date: 2026-02-05
License: Apache-2.0
"""

import sqlite3
from collections.abc import Generator

import pytest

from depo.repo.sqlite import SqliteRepository, init_db
from depo.service.ingest import IngestService
from depo.service.orchestrator import IngestOrchestrator
from depo.storage.filesystem import FilesystemStorage

from .db import test_db

# TODO: Remove when refactor complete
# Temporary aliases until migration complete
from .storage import tmp_fs  # noqa


@pytest.fixture
def conn() -> Generator[sqlite3.Connection, None, None]:  # noqa: F811
    """Temporary alias for t_conn."""
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


@pytest.fixture
def t_conn() -> Generator[sqlite3.Connection, None, None]:
    """Raw in-memory SQLite connection (no schema)."""
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


@pytest.fixture
def t_db() -> Generator[sqlite3.Connection, None, None]:
    """In-memory SQLite repository with schema."""
    c = sqlite3.connect(":memory:")
    init_db(c)
    yield c
    c.close()


@pytest.fixture
def t_repo(t_db) -> SqliteRepository:
    """SqliteRepository instance using in-memory DB."""
    return SqliteRepository(t_db)


@pytest.fixture
def t_store(tmp_path) -> FilesystemStorage:
    """FilesystemStorage instance with temporary root."""
    return FilesystemStorage(root=tmp_path / "depo-test-store")


@pytest.fixture
def t_orch_env(
    t_repo, t_store
) -> tuple[IngestOrchestrator, SqliteRepository, FilesystemStorage]:
    service = IngestService()
    orch = IngestOrchestrator(service, t_repo, t_store)
    return (orch, t_repo, t_store)


@pytest.fixture
def test_store(tmp_path):
    """FilesystemStorage instance with temporary root."""
    return FilesystemStorage(root=tmp_path / "depo-test-store")


@pytest.fixture
def test_orchestrator_env(test_db, tmp_fs):
    """Returns (orchestrator, repo, storage) tuple"""
    service = IngestService()
    repo = SqliteRepository(test_db)
    orch = IngestOrchestrator(service, repo, tmp_fs)
    return (orch, repo, tmp_fs)


__all__ = [
    "test_db",
    "test_store",
    "test_orchestrator_env",
    "tmp_fs",
    # "test_storage",
    # "test_storage_root",
    # TODO: Refactor & rm entries once we've confirmed modules no longer use old
    "t_conn",
    "t_db",
    "t_store",
    "t_repo",
    "t_orch_env",
]
