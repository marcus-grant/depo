# tests/storage/test_filesystem.py
"""
Tests for storage/filesystem.py FilesystemStorage.

Author: Marcus Grant
Date: 2026-02-03
License: Apache-2.0
"""

import pytest

from depo.model.enums import ContentFormat
from depo.model.formats import extension_for_format
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

    def test_writes_source_bytes_to_correct_path(self, t_store):
        """Writes source_bytes to {root}/{code}.{ext}"""
        # Use format TIFF to prove extension_for_format is used: TIFF -> .tif
        f2e, f1, f2 = extension_for_format, ContentFormat.PLAINTEXT, ContentFormat.TIFF
        c1, c2, e1, e2 = "ABC123", "XYZ789", f2e(f1), f2e(f2)
        t_store.put(code=c1, format=f1, source_bytes=b"hello")
        t_store.put(code=c2, format=f2, source_bytes=b"\x00\xff\x00")
        assert (t_store._root / f"{c1}.{e1}").read_bytes() == b"hello"
        assert (t_store._root / f"{c2}.{e2}").read_bytes() == b"\x00\xff\x00"

    def test_writes_source_path_to_correct_path(self, t_store):
        """Writes source_path contents to {root}/{code}.{ext}"""
        # Assemble temporary files with test data
        path_jpg, byt_jpg = (t_store._root / "input.jpg"), b"hello"
        path_tif, byt_tif = (t_store._root / "input.tif"), b"\x00\xff\x00"
        path_jpg.write_bytes(byt_jpg)
        path_tif.write_bytes(byt_tif)
        # Act
        t_store.put(code="jpg12345", format=ContentFormat.JPEG, source_path=path_jpg)
        t_store.put(code="tifmpqrs", format=ContentFormat.TIFF, source_path=path_tif)
        # Assert
        assert (t_store._root / "jpg12345.jpg").read_bytes() == byt_jpg
        assert (t_store._root / "tifmpqrs.tif").read_bytes() == byt_tif

    def test_raises_for_none_or_both_source_args(self, t_store):
        """Raises for both source_* args being both None or both valid values"""
        err = r"(?i)one of.*source"
        with pytest.raises(ValueError, match=err):
            t_store.put(code="f00bar", format=ContentFormat.PNG)
        with pytest.raises(ValueError, match=err):
            kw = {"code": "f00bar", "format": ContentFormat.PNG}
            t_store.put(**kw, source_bytes=b"hi", source_path=t_store._root)


class TestFilesystemStorageOpen:
    """Tests FilesystemStorage.open()."""

    def test_file_handle_for_existing_file(self, t_store):
        """Returns file handle for existing file"""
        # Assemble existing test file & expected inputs
        code, fmt, data = "19F00BAR", ContentFormat.JSON, b"FooBar"
        t_store.put(code=code, format=fmt, source_bytes=data)
        # Act by opening put test file
        with t_store.open(code=code, format=fmt) as f:
            # Assert by comparing put data with opened
            assert f.read() == data

    def test_raises_for_no_file(self, t_store):
        """Raises FileNotFoundError for missing file"""
        with pytest.raises(FileNotFoundError):
            t_store.open(code="N0TEX1ST", format=ContentFormat.PNG)


class TestFilesystemStorageDelete:
    """Tests FilesystemStorage.delete()."""

    def test_removes_existing_file(self, t_store):
        """Removes existing file"""
        # Assemble existing test file with code and format
        code, fmt, data = "F1LEX1ST", ContentFormat.PLAINTEXT, b"Hello, World!"
        t_store.put(code=code, format=fmt, source_bytes=data)
        # Act by using delete() on existing test file
        t_store.delete(code=code, format=fmt)
        # Assert the file no longer exists by using .open to raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            t_store.open(code=code, format=fmt)

    def test_no_error_for_missing_file(self, t_store):
        """No error when attempting to delete non-existing file"""
        # Act by delete() on non-existing file - asserts by not raising
        t_store.delete(code="N0TEX1ST", format=ContentFormat.PNG)
