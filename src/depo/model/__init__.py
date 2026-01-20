# src/depo/model/__init__.py
"""
Domain models, DTOs, and enums.

Pure Python with no I/O dependencies.
Only meant to structure and contain data.

Author: Marcus Grant
Date: 2026-01-20
License: Apache-2.0
"""

from depo.model.enums import ItemKind, PayloadKind, Visibility
from depo.model.item import Item, LinkItem, PicItem, TextItem
from depo.model.write_plan import WritePlan

__all__ = [
    "ItemKind",
    "PayloadKind",
    "Visibility",
    "Item",
    "TextItem",
    "PicItem",
    "LinkItem",
    "WritePlan",
]
