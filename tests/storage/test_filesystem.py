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

    def test_writes_source_bytes_to_correct_path(self, tmp_fs):
        """Writes source_bytes to {root}/{code}.{ext} & ext from extension_for_format"""
        # Assemble shortened format references
        cf_txt, cf_tif = ContentFormat.PLAINTEXT, ContentFormat.TIFF

        # Act on test bytes 0x00ff00 is an edge case for empty file headers
        # TIFF proves extension_for_format is used (special case TIFF -> tif)
        tmp_fs.put(code="ABC123", format=cf_txt, source_bytes=b"hello")
        tmp_fs.put(code="XYZ789", format=cf_tif, source_bytes=b"\x00\xff\x00")

        # Assert test bytes are readable from expected paths
        path_txt = tmp_fs._root / f"ABC123.{extension_for_format(cf_txt)}"
        path_tif = tmp_fs._root / f"XYZ789.{extension_for_format(cf_tif)}"
        assert path_txt.read_bytes() == b"hello"
        assert path_tif.read_bytes() == b"\x00\xff\x00"

    def test_writes_source_path_to_correct_path(self, tmp_fs):
        """Writes source_path contents to {root}/{code}.{ext} uses ext.._format"""
        # Assemble temporary file paths with test data
        tmp_jpg, tmp_tif = tmp_fs._root / "jpeg.tmp", tmp_fs._root / "tif.tmp"
        tmp_jpg.write_bytes(b"hello")
        tmp_tif.write_bytes(b"\x00\xff\x00")
        cf_jpg, cf_tif = ContentFormat.JPEG, ContentFormat.TIFF  # shorten references

        # Act with temp file paths
        tmp_fs.put(code="jpg12345", format=cf_jpg, source_path=tmp_jpg)
        tmp_fs.put(code="tifmpqrs", format=cf_tif, source_path=tmp_tif)

        # Assert same data in expected paths made by extension_for_format
        path_jpg = tmp_fs._root / f"jpg12345.{extension_for_format(cf_jpg)}"
        path_tif = tmp_fs._root / f"tifmpqrs.{extension_for_format(cf_tif)}"
        assert path_jpg.read_bytes() == b"hello"
        assert path_tif.read_bytes() == b"\x00\xff\x00"

    def test_raises_for_none_or_both_source_args(self, tmp_fs):
        """Raises for both source_* args being both None or both valid values"""
        err = r"(?i)one of.*source"
        base_kwargs = {"code": "f00bar", "format": ContentFormat.PNG}
        with pytest.raises(ValueError, match=err):
            # Raise when both source_* args are None
            tmp_fs.put(**base_kwargs)
        with pytest.raises(ValueError, match=err):
            # Raise when both source_* args are valid values
            tmp_fs.put(**base_kwargs, source_bytes=b"hi", source_path=tmp_fs._root)


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


