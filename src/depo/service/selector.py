# src/depo/service/selector.py
"""
Read-path selectors for content items.

Services write, selectors read. Module-level functions
that operate on repo and storage dependencies.

Author: Marcus Grant
Created: 2026-02-06
License: Apache-2.0
"""

from typing import BinaryIO

from depo.model.item import LinkItem, PicItem, TextItem
from depo.repo.errors import NotFoundError
from depo.repo.sqlite import SqliteRepository
from depo.storage.protocol import StorageBackend


def get_item(repo: SqliteRepository, code: str) -> TextItem | PicItem | LinkItem:
    """
    Fetch item by short code.

    Args:
        repo: Repository instance.
        code: Short code identifier.

    Returns:
        Resolved item.

    Raises:
        NotFoundError: If code not found.
    """
    if item := repo.get_by_code(code):
        return item
    raise NotFoundError(code)


def get_raw(
    repo: SqliteRepository, storage: StorageBackend, code: str
) -> tuple[BinaryIO | None, TextItem | PicItem | LinkItem]:
    """
    Fetch item and its payload handle.

    Args:
        repo: Repository instance.
        storage: Storage backend.
        code: Short code identifier.

    Returns:
        (file_handle, item) for TextItem/PicItem; (None, item) for LinkItem.

    Raises:
        NotFoundError: If code not found.
    """
    raise NotImplementedError


def get_info(repo: SqliteRepository, code: str) -> TextItem | PicItem | LinkItem:
    """
    Fetch item metadata. Thin wrapper today, seam for future enrichment.

    Args:
        repo: Repository instance.
        code: Short code identifier.

    Returns:
        Resolved item.

    Raises:
        NotFoundError: If code not found.
    """
    raise NotImplementedError
