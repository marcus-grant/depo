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


class TestFilesystemStoragePut:
    """Tests FilesystemStorage.put()."""

    def test_writes_source_bytes_to_correct_path(self, tmp_fs):
        """Writes source_bytes to {root}/{code}.{ext}"""
        tmp_fs.put(code="ABC123", format=ContentFormat.PLAINTEXT, source_bytes=b"hello")
        tmp_fs.put(
            code="XYZ789", format=ContentFormat.TIFF, source_bytes=b"\x00\xff\x00"
        )
        # TIFF -> tif proves extension_for_format is used
        assert (tmp_fs._root / "ABC123.txt").read_bytes() == b"hello"
        assert (tmp_fs._root / "XYZ789.tif").read_bytes() == b"\x00\xff\x00"

    def test_writes_source_path_to_correct_path(self, tmp_fs):
        """Writes source_path contents to {root}/{code}.{ext}"""
        # Assemble temporary files with test data
        tmp_jpg = tmp_fs._root / "input.jpg"
        tmp_tif = tmp_fs._root / "input.tif"
        tmp_jpg.write_bytes(b"hello")
        tmp_tif.write_bytes(b"\x00\xff\x00")
        # Act
        tmp_fs.put(code="jpg12345", format=ContentFormat.JPEG, source_path=tmp_jpg)
        tmp_fs.put(code="tifmpqrs", format=ContentFormat.TIFF, source_path=tmp_tif)
        # Assert
        assert (tmp_fs._root / "jpg12345.jpg").read_bytes() == b"hello"
        assert (tmp_fs._root / "tifmpqrs.tif").read_bytes() == b"\x00\xff\x00"

    def test_raises_for_none_or_both_source_args(self, tmp_fs):
        """Raises for both source_* args being both None or both valid values"""
        err = r"(?i)one of.*source"
        with pytest.raises(ValueError, match=err):
            tmp_fs.put(code="f00bar", format=ContentFormat.PNG)
        with pytest.raises(ValueError, match=err):
            tmp_fs.put(
                code="f00bar",
                format=ContentFormat.PNG,
                source_bytes=b"hi",
                source_path=tmp_fs._root,
            )


class TestFilesystemStorageOpen:
    """Tests FilesystemStorage.open()."""

    def test_file_handle_for_existing_file(self, tmp_fs):
        """Returns file handle for existing file"""
        # Assemble existing test file & expected inputs
        code, fmt, data = "19F00BAR", ContentFormat.JSON, b"FooBar"
        tmp_fs.put(code=code, format=fmt, source_bytes=data)

        # Act by opening put test file
        with tmp_fs.open(code=code, format=fmt) as f:
            # Assert by comparing put data with opened
            assert f.read() == data

    def test_raises_for_no_file(self, tmp_fs):
        """Raises FileNotFoundError for missing file"""
        with pytest.raises(FileNotFoundError):
            tmp_fs.open(code="N0TEX1ST", format=ContentFormat.PNG)


class TestFilesystemStorageDelete:
    """Tests FilesystemStorage.delete()."""

    def test_removes_existing_file(self, tmp_fs):
        """Removes existing file"""
        # Assemble existing test file with code and format
        code, fmt, data = "F1LEX1ST", ContentFormat.PLAINTEXT, b"Hello, World!"
        tmp_fs.put(code=code, format=fmt, source_bytes=data)

        # Act by using delete() on existing test file
        tmp_fs.delete(code=code, format=fmt)

        # Assert the file no longer exists by using .open to raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            tmp_fs.open(code=code, format=fmt)

    def test_no_error_for_missing_file(self, tmp_fs):
        """No error when attempting to delete non-existing file"""
        # Act by delete() on non-existing file - asserts by not raising
        tmp_fs.delete(code="N0TEX1ST", format=ContentFormat.PNG)
