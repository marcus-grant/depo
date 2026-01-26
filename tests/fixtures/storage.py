# tests/fixtures/storage.py
"""
Storage fixtures for filesystem backend testing.
Author: Marcus Grant
Date: 2026-01-26
License: Apache-2.0
"""

import pytest


@pytest.fixture
def test_storage_root():
    """Temporary directory for storage tests."""
    # TODO: Implement in PR 4 (storage layer)
    raise NotImplementedError("test_storage_root fixture not yet implemented")


@pytest.fixture
def test_storage():
    """FilesystemStorage instance with temporary root."""
    # TODO: Implement in PR 4 (storage layer)
    raise NotImplementedError("test_storage fixture not yet implemented")
