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
from depo.service.ingest import IngestService
from depo.service.orchestrator import IngestOrchestrator, PersistResult
from depo.util.shortcode import hash_full_b32

_EXPECTED_OS_RAISE = "Testing disk write error"


def _failing_put(**_):
    raise OSError(_EXPECTED_OS_RAISE)


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

    def test_stores_all_members(self, t_repo, t_store):
        """Stores IngestOrchestrator expected members"""
        service = IngestService()
        orchestrator = IngestOrchestrator(service, t_repo, t_store)
        assert orchestrator._service is service
        assert orchestrator._repo is t_repo
        assert orchestrator._store is t_store


class TestIngestOrchestratorIngest:
    """Tests for IngestOrchestrator.ingest()."""

    def test_happy_path_text_item(self, t_orch_env):
        """TextItem happy path: created=True, item in repo, bytes in storage."""
        orch, repo, store = t_orch_env  # Assemble orchestrator
        payload, fmt = b"Hello, World!", ContentFormat.PLAINTEXT
        # Act with assembled orchestrator's ingest & test inputs
        result = orch.ingest(payload_bytes=payload, requested_format=fmt)
        # Assert PersistResult with correct field values
        assert isinstance(result, PersistResult)
        assert result.created
        assert repo.get_by_full_hash(result.item.hash_full) == result.item
        assert isinstance(result.item, TextItem)
        with store.open(code=result.item.code, format=result.item.format) as f:
            assert f.read() == payload

    def test_happy_path_pic_item(self, t_orch_env):
        """PicItem happy path: created=True, item in repo, bytes in storage."""
        # TODO: Modify this test to use payload_path file streaming
        orch, repo, storage = t_orch_env  # Assemble orchestrator
        payload = gen_image(ContentFormat.PNG, 1, 1)  # and its inputs
        result = orch.ingest(payload_bytes=payload)  # Act
        assert isinstance(result, PersistResult)  # Assert
        assert result.created
        assert repo.get_by_full_hash(result.item.hash_full) == result.item
        assert isinstance(result.item, PicItem)
        with storage.open(code=result.item.code, format=result.item.format) as f:
            assert f.read() == payload

    def test_happy_path_link_item(self, t_orch_env):
        """LinkItem happy path: created=True, item in repo, NOT in storage."""
        orch, repo, store = t_orch_env  # Assemble
        result = orch.ingest(link_url="https://www.example.com/")  # Act
        assert isinstance(result, PersistResult)  # Assert
        assert result.created
        assert repo.get_by_full_hash(result.item.hash_full) == result.item
        assert isinstance(result.item, LinkItem)
        assert list(store._root.glob(f"*{result.item.code}*")) == []

    def test_dedupe_returns_existing_item(self, t_orch_env):
        """Duplicate payload returns created=False with existing item."""
        # Assemble Orchestrator, and the payload to ingest
        orch, _, _ = t_orch_env
        payload, fmt = b"duplicate content", ContentFormat.PLAINTEXT

        # Act by ingesting the same content twice with same args
        first = orch.ingest(payload_bytes=payload, requested_format=fmt)
        second = orch.ingest(payload_bytes=payload, requested_format=fmt)

        # Assert only first result has .created and that first.item == second.item
        assert first.created is True
        assert second.created is False
        assert second.item == first.item

    def test_rollback_on_storage_raise(self, t_orch_env, monkeypatch):
        """Rollback on storage.put OSError causes repo.delete & re-raises"""
        orch, repo, store = t_orch_env
        monkeypatch.setattr(store, "put", _failing_put)
        hash_full, cf_txt = hash_full_b32(b"hello"), ContentFormat.PLAINTEXT
        with pytest.raises(OSError, match=_EXPECTED_OS_RAISE):
            orch.ingest(payload_bytes=b"hello", requested_format=cf_txt)
        assert repo.get_by_full_hash(hash_full) is None
