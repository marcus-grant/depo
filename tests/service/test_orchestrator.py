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
from tests.factories.payloads import gen_image
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
        assert orchestrator._service is service
        assert orchestrator._repo is repo
        assert orchestrator._store is tmp_fs


class TestIngestOrchestratorIngest:
    """Tests for IngestOrchestrator.ingest()."""

    def test_happy_path_text_item(self, test_orchestrator_env):
        """TextItem happy path: created=True, item in repo, bytes in storage."""
        orch, repo, store = test_orchestrator_env
        payload, fmt = b"Hello, World!", ContentFormat.PLAINTEXT

        result = orch.ingest(payload_bytes=payload, requested_format=fmt)
        item, hash_full, code = result.item, result.item.hash_full, result.item.code

        assert isinstance(result, PersistResult)
        assert result.created
        assert repo.get_by_full_hash(hash_full) == item
        assert isinstance(item, TextItem)
        with store.open(code=code, format=item.format) as f:
            assert f.read() == payload

    def test_happy_path_pic_item(self, test_orchestrator_env):
        """PicItem happy path: created=True, item in repo, bytes in storage."""
        orch, repo, storage = test_orchestrator_env
        payload = gen_image(ContentFormat.PNG, 1, 1)
        # TODO: Modify this test to use payload_path file streaming

        result = orch.ingest(payload_bytes=payload)
        item, hash_full, code = result.item, result.item.hash_full, result.item.code

        assert isinstance(result, PersistResult)
        assert result.created
        assert repo.get_by_full_hash(hash_full) == item
        assert isinstance(item, PicItem)
        with storage.open(code=code, format=item.format) as f:
            assert f.read() == payload

    def test_happy_path_link_item(self, test_orchestrator_env):
        """LinkItem happy path: created=True, item in repo, NOT in storage."""
        # Assemble orchestrator, its repo and its store
        orch, repo, store = test_orchestrator_env

        result = orch.ingest(link_url="https://www.example.com/")
        item, hash_full, code = result.item, result.item.hash_full, result.item.code

        assert isinstance(result, PersistResult)
        assert result.created
        assert repo.get_by_full_hash(hash_full) == item
        assert isinstance(item, LinkItem)
        assert list(store._root.glob(f"*{code}*")) == []

    def test_dedupe_returns_existing_item(self, test_orchestrator_env):
        """Duplicate payload returns created=False with existing item."""
        # Assemble Orchestrator, and the payload to ingest
        orch, _, _ = test_orchestrator_env
        payload, fmt = b"duplicate content", ContentFormat.PLAINTEXT

        # Act by ingesting the same content twice with same args
        first = orch.ingest(payload_bytes=payload, requested_format=fmt)
        second = orch.ingest(payload_bytes=payload, requested_format=fmt)

        # Assert only first result has .created and that first.item == second.item
        assert first.created is True
        assert second.created is False
        assert second.item == first.item


# Dedupe:
# - existing hash → returns PersistResult with created=False
# - existing hash → returns existing item, no new insert
# - existing hash → storage.put not called
