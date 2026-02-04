# tests/service/test_orchestrator.py
"""
Tests for orchestrator module.

Author: Marcus Grant
Date: 2026-02-03
License: Apache-2.0
"""

from dataclasses import FrozenInstanceError

import pytest
from tests.factories.models import make_link_item, make_pic_item, make_text_item
from tests.helpers.assertions import assert_field

from depo.model.enums import ContentFormat
from depo.model.item import LinkItem, PicItem, TextItem
from depo.repo.sqlite import SqliteRepository
from depo.service.ingest import IngestService
from depo.service.orchestrator import IngestOrchestrator, PersistResult


class TestPersistResult:
    """Tests for PersistResult DTO."""

    @pytest.mark.parametrize(
        ("name", "typ", "required", "default"),
        [
            ("item", LinkItem | PicItem | TextItem, True, None),
            ("created", bool, True, None),
        ],
    )
    def test_correct_fields(self, name, typ, required, default):
        """Field properties (name, type, required, default value) are correct."""
        assert_field(PersistResult, name, typ, required, default)

    def test_frozen_dataclass(self):
        """Is a frozen dataclass"""
        obj = PersistResult(item=make_link_item(), created=True)
        assert isinstance(obj, PersistResult)
        with pytest.raises(FrozenInstanceError):
            obj.created = False  # type: ignore

    def test_accepts_all_item_kinds(self):
        """Can be instantiated with any Item subtype."""
        for factory in [make_text_item, make_pic_item, make_link_item]:
            item = factory()
            result = PersistResult(item=item, created=False)
            assert result.item is item, f"Failed for {type(item).__name__}"


class TestIngestOrchestratorInit:
    """Tests for IngestOrchestrator constructor."""

    def test_stores_all_members(self, test_db, tmp_fs):
        """Stores IngestOrchestrator expected members"""
        service, repo = IngestService(), SqliteRepository(test_db)
        orchestrator = IngestOrchestrator(service, repo, tmp_fs)
        assert orchestrator._service == service
        assert orchestrator._repo == repo
        assert orchestrator._store == tmp_fs


class TestIngestOrchestratorIngest:
    """Tests for IngestOrchestrator.ingest()."""

    def test_happy_path(self, test_db, tmp_fs):
        """Happy path returns
        - PersistedResult.created=True
        - item persisted in repo
        - bytes written to storage"""
        # Assemble orchestrator inputs and basic ingest args
        payload, fmt = b"Hello, World!", ContentFormat.PLAINTEXT
        service, repo = IngestService(), SqliteRepository(test_db)
        orchestrator = IngestOrchestrator(service, repo, tmp_fs)

        # Act with ingest in happy path and collect PersistedResult & item fields
        result = orchestrator.ingest(payload_bytes=payload, requested_format=fmt)
        item, hash_full, code = result.item, result.item.hash_full, result.item.code

        # Assert result.created == True, item in repo, content in store
        assert isinstance(result, PersistResult)
        assert result.created
        assert repo.get_by_full_hash(hash_full) == item
        assert isinstance(item, TextItem)
        with tmp_fs.open(code=code, format=item.format) as f:
            assert f.read() == payload


# Happy path:
# - returns PersistResult with created=True
# - item persisted in repo (get_by_full_hash returns it)
# - bytes written to storage (storage.open returns content)
