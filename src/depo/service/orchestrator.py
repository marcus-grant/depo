# src/depo/service/orchestrator.py
"""
Ingest orchestration.

Coordinates IngestService, Repository, and Storage for the full
ingest pipeline. Single entry point for web layer.

Author: Marcus Grant
Date: 2026-02-03
License: Apache-2.0
"""

from dataclasses import dataclass

from depo.model.item import LinkItem, PicItem, TextItem


@dataclass(frozen=True)
class PersistResult:
    """Result of ingest operation.

    Attributes:
        item: The persisted item (new or existing).
        created: True if newly created, False if deduplicated.
    """

    item: LinkItem | PicItem | TextItem
    created: bool
