# tests/fixtures/storage.py
"""
Storage fixtures for filesystem backend testing.
Author: Marcus Grant
Date: 2026-01-26
License: Apache-2.0
"""

import pytest

from src.depo.storage.filesystem import FilesystemStorage


@pytest.fixture
def test_storage_root(tmp_path):
    """Temporary directory for storage tests."""
    return tmp_path / "storage"


@pytest.fixture
def test_storage(test_storage_root):
    """FilesystemStorage instance with temporary root."""
    return FilesystemStorage(root=test_storage_root)
