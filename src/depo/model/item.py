# src/depo/model/item.py
"""
Domain models for content items.

Defines Item base class & its subtypes: TextItem, PicItem, LinkItem, etc.
These are pure, frozen dataclasses representing content-addressed items.
No I/O or framework dependencies.

Author: Marcus Grant
Date: 2026-01-19
License: Apache-2.0
"""

from dataclasses import dataclass

from depo.model.enums import ItemKind, Visibility


@dataclass(frozen=True)
class Item:
    code: str
    hash_rest: str
    kind: ItemKind
    mime: str
    size_b: int
    created_at: int
    uid: int
    perm: Visibility = Visibility.PUBLIC
