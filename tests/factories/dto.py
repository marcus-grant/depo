# tests/factories/dto.py
"""
DTO test factories.

Builds domain DTOs for unit tests without requiring
database or storage setup.

Author: Marcus Grant
Created: 2026-02-10
License: Apache-2.0
"""

from depo.model.enums import ContentFormat, ItemKind, Visibility
from depo.model.item import LinkItem, PicItem, TextItem
from depo.service.orchestrator import PersistResult


def make_persist_result(
    *,
    item: TextItem | PicItem | LinkItem | None = None,
    created: bool = True,
) -> PersistResult:
    """Build a PersistResult with sensible defaults."""
    if item is None:
        item = TextItem(
            hash_full="0123456789ABCDEFGHJKMNPQ",
            code="01234567",
            kind=ItemKind.TEXT,
            size_b=99,
            uid=0,
            perm=Visibility.PUBLIC,
            upload_at=123456789,
            origin_at=None,
            format=ContentFormat.PLAINTEXT,
        )
    return PersistResult(item=item, created=created)
