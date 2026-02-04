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
from depo.repo.sqlite import SqliteRepository
from depo.service.ingest import IngestService
from depo.storage.protocol import StorageBackend


@dataclass(frozen=True)
class PersistResult:
    """Result of ingest operation.

    Attributes:
        item: The persisted item (new or existing).
        created: True if newly created, False if deduplicated.
    """

    item: LinkItem | PicItem | TextItem
    created: bool


class IngestOrchestrator:
    """Coordinates ingest pipeline between service, repo, and storage."""

    def __init__(
        self,
        ingest_service: IngestService,
        repo: SqliteRepository,
        store: StorageBackend,
    ) -> None:
        """Initialize with dependencies.

        Args:
            ingest_service: Service for building WritePlans.
            repo: Repository for persistence.
            storage: Backend for file storage.
        """
        self._service = ingest_service
        self._repo = repo
        self._store = store
