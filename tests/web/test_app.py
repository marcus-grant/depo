# tests/web/test_app.py
"""
Tests for the FastAPI app factory and health check.

Author: Marcus Grant
Created: 2026-02-09
License: Apache-2.0
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from depo.cli.config import DepoConfig
from depo.web.app import app_factory


# TODO: Move to fixture/factory when close to MVP? For all helpers below?
def _depo_cfg_kwargs(p: Path) -> dict:
    return {"db_path": p / "depo.db", "store_root": p / "store"}


def _depo_cfg(p: Path) -> DepoConfig:
    return DepoConfig(**_depo_cfg_kwargs(p))


def _make_client(p: Path) -> TestClient:
    """Build a TestClient from a DepoConfig pointing at tmp_path."""
    return TestClient(app_factory(_depo_cfg(p)))


class TestAppFactory:
    """Tests for app_factory()."""

    def test_returns_fastapi_instance(self, tmp_path):
        """Returns a FastAPI instance"""
        config = DepoConfig(**_depo_cfg_kwargs(tmp_path))
        assert isinstance(app_factory(config), FastAPI)

    def test_depo_config_accessible(self, tmp_path):
        """Returned FastAPI instance has accessible DepoConfig in app.state"""
        config = DepoConfig(**_depo_cfg_kwargs(tmp_path))
        assert app_factory(config).state.config is config


class TestHealthCheck:
    """Tests for GET /health."""

    def test_health_returns_200_plaintext(self, tmp_path):
        """Response to /health is 200 with useful plaintext response"""
        client = _make_client(tmp_path)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/plain")
        assert resp.text == "ok"
