# tests/storage/test_filesystem.py
"""
Tests for storage/filesystem.py FilesystemStorage.

Author: Marcus Grant
Date: 2026-02-03
License: Apache-2.0
"""

import pytest

from depo.model.enums import ContentFormat
from depo.storage.filesystem import FilesystemStorage


class TestFilesystemStorageInit:
    """Tests FilesystemStorage constructor."""

    def test_creates_root_dir_if_missing(self, tmp_path):
        """Test that the root directory is created if it doesn't exist."""
        root = tmp_path / "depo"
        assert not root.exists()
        FilesystemStorage(root=root)
        assert root.is_dir()

    def test_accepts_existing_root_dir(self, tmp_path):
        """Test that an existing directory is accepted as root."""
        root = tmp_path / "depo"
        root.mkdir()
        assert root.is_dir()
        storage = FilesystemStorage(root=root)
        assert root.is_dir()
        assert isinstance(storage, FilesystemStorage)

    def test_stores_root_path(self, tmp_path):
        """Test that the root path is stored correctly."""
        storage = FilesystemStorage(root=tmp_path / "depo")
        assert storage._root == tmp_path / "depo"


