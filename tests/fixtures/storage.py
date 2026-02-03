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
def tmp_fs(tmp_path):
    """FilesystemStorage instance with temporary root."""
    return FilesystemStorage(root=tmp_path / "depo-test")
