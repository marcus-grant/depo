# tests/service/test_selector.py
"""
Tests for selector read-path functions.

Author: Marcus Grant
Created: 2026-02-06
License: Apache-2.0
"""

import pytest
from tests.factories.db import seed_all_types

from depo.repo.errors import NotFoundError
from depo.service.selector import get_info, get_item, get_raw


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

    # - returns (file_handle, item) for TextItem/PicItem
    # - returns (None, item) for LinkItem
    # - raises NotFoundError when code missing


class TestGetInfo:
    """Tests for get_info()."""

    # - returns item when code exists
    # - raises NotFoundError when code missing
