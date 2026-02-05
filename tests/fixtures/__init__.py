# tests/fixtures/__init__.py
"""Re-exports for test fixtures."""

import pytest

from depo.repo.sqlite import SqliteRepository
from depo.service.ingest import IngestService
from depo.service.orchestrator import IngestOrchestrator
from depo.storage.filesystem import FilesystemStorage

from .db import test_db

# TODO: Uncomment as implemented
# from .storage import test_storage, test_storage_root


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
    # "test_storage",
    # "test_storage_root",
]
