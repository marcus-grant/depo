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


__all__ = [
    "t_conn",
    "t_db",
    "t_store",
    "t_repo",
    "t_orch_env",
]
