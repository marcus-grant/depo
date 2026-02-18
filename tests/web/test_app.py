# tests/web/test_app.py
"""
Tests for the FastAPI app factory and health check.

Author: Marcus Grant
Created: 2026-02-09
License: Apache-2.0
"""

from fastapi import FastAPI

from depo.web.app import app_factory
from tests.factories import make_config


class TestAppFactory:
    """Tests for app_factory()."""

    def test_returns_fastapi_instance(self, tmp_path):
        """Returns a FastAPI instance"""
        assert isinstance(app_factory(make_config(tmp_path)), FastAPI)

    def test_depo_config_accessible(self, tmp_path):
        """Returned FastAPI instance has accessible DepoConfig in app.state"""
        config = make_config(tmp_path)
        assert app_factory(config).state.config is config


class TestHealthCheck:
    """Tests for GET /health."""

    def test_health_returns_200_plaintext(self, t_client):
        """Response to /health is 200 with useful plaintext response"""
        resp = t_client.get("/health")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/plain")
        assert resp.text == "ok"
