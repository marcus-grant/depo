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
from pathlib import Path

from depo.model.enums import Visibility
from depo.model.formats import ContentFormat
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

    def ingest(
        self,
        *,
        payload_bytes: bytes | None = None,
        payload_path: Path | None = None,
        filename: str | None = None,
        declared_mime: str | None = None,
        requested_format: ContentFormat | None = None,
        uid: int = 0,
        perm: Visibility = Visibility.PUBLIC,
    ) -> PersistResult:
        """Ingest content and persist to repo and storage.

        Args:
            payload_bytes: Content as in-memory bytes.
            payload_path: Path to content on disk.
            filename: Original filename hint.
            declared_mime: MIME type from HTTP header.
            requested_format: Explicit format requested by user.
            uid: User ID.
            perm: Visibility level.

        Returns:
            PersistResult with item and created flag.

        Raises:
            ValueError: If validation or classification fails.
        """
        plan = self._service.build_plan(
            payload_bytes=payload_bytes,
            payload_path=payload_path,
            filename=filename,
            declared_mime=declared_mime,
            requested_format=requested_format,
        )  # First build WritePlan with IngestService

        # Insert into database with WritePlan
        item = self._repo.insert(plan)

        # Save into StorageBackend
        self._store.put(code=item.code, format=item.format, source_bytes=payload_bytes)  # type: ignore

        # Return PersistResult as result of IngestOrchestrator pipeline
        return PersistResult(item=item, created=True)
