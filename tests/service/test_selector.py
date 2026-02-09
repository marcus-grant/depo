# tests/service/test_selector.py
"""
Tests for selector read-path functions.

Author: Marcus Grant
Created: 2026-02-06
License: Apache-2.0
"""

import pytest
from tests.factories.db import insert_pic_item, insert_text_item, seed_all_types

from depo.repo.errors import NotFoundError
from depo.service.selector import get_item, get_raw
from depo.storage.filesystem import FilesystemStorage as FsStore


class TestGetItem:
    """Tests for get_item()."""

    def test_item_when_code_exists(self, t_db, t_repo):
        """Returns correct Item when code exists as Item"""
        txt_item, pic_item, link_item = seed_all_types(t_db)
        assert get_item(t_repo, txt_item.code) == txt_item
        assert get_item(t_repo, pic_item.code) == pic_item
        assert get_item(t_repo, link_item.code) == link_item

    def test_raises_not_found_when_code_missing(self, t_repo):
        """Raises NotFoundError when code missing"""
        with pytest.raises(NotFoundError):
            get_item(t_repo, "N0TEX1ST")


class TestGetRaw:
    """Tests for get_raw()."""

    def test_returns_correct_txt_handle(self, t_db, t_store: FsStore):
        """Returns correct file handle with expected txt content when it exists."""
        item = insert_text_item(t_db, code="TXT5678")
        content = b"# Hello, World!"
        t_store.put(code=item.code, format=item.format, source_bytes=content)
        with get_raw(t_store, item) as f:
            assert f.read() == content

    def test_returns_correct_pic_handle(self, t_db, t_store: FsStore):
        """Returns correct file handle with expected pic content when it exists."""
        item = insert_pic_item(t_db, code="PIC5678")
        content = b"\xff\xd8\xff\x00"
        t_store.put(code=item.code, format=item.format, source_bytes=content)
        with get_raw(t_store, item) as f:
            assert f.read() == content
