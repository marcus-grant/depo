# tests/web/test_app.py
"""
Tests for the FastAPI app factory and health check.

Author: Marcus Grant
Created: 2026-02-09
Revised: [2026-06-23]
License: Apache-2.0
"""

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from depo.util.errors import AuthRequiredError
from depo.web.app import app_factory
from depo.web.deps import get_current_uid
from tests.factories import make_config, make_full_probe_client


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


class TestConfigWiring:
    """Resolved config governs the live upload path (gating tests)."""

    def test_max_size_bytes_governs(self, tmp_path):
        """A tiny max_size_bytes rejects any upload with 413."""
        client = TestClient(app_factory(make_config(tmp_path, max_size_bytes=1)))
        resp = client.post("/upload", files={"file": ("t.txt", b"too big")})
        assert resp.status_code == 413

    def test_max_url_len_governs(self, tmp_path):
        """A tiny max_url_len rejects a link with 413."""
        client = TestClient(app_factory(make_config(tmp_path, max_url_len=1)))
        resp = client.post("/upload?url=http://example.com")
        assert resp.status_code == 413

    def test_min_code_len_governs(self, tmp_path):
        """A raised min_code_length yields a code of exactly that length."""
        client = TestClient(app_factory(make_config(tmp_path, min_code_len=12)))
        resp = client.post("/upload", files={"file": ("t.txt", b"hello world")})
        assert len(resp.headers["X-Depo-Code"]) == 12


class TestSessionMiddleware:
    """Tests that SessionMiddleware is wired and the current-user seam works."""

    def _uid_probe(self, request: Request):
        return {"uid": get_current_uid(request)}  # should not raise

    def test_session_available_in_handler(self, tmp_path):
        """A handler can read and write request.session without error."""

        def _session_probe(request: Request):
            request.session["probe"] = "ok"
            return {"probe": request.session["probe"]}

        resp = make_full_probe_client(tmp_path, _session_probe).get("/test/probe")
        assert resp.status_code == 200
        assert resp.json()["probe"] == "ok"

    def test_unauthenticated_request_has_no_uid(self, tmp_path):
        """get_current_uid returns None for a request with no session uid."""
        client = make_full_probe_client(tmp_path, self._uid_probe)
        assert client.get("/test/probe").json()["uid"] is None

    def test_tampered_cookie_rejected(self, tmp_path):
        """A forged or tampered session cookie resolves to no current user."""
        client = make_full_probe_client(tmp_path, self._uid_probe)
        client.cookies.set("session", "bad_cookie")
        assert client.get("/test/probe").json()["uid"] is None

    def test_uid_round_trips_as_int(self, tmp_path):
        """A uid written to the session is returned by get_current_uid as int."""

        def _set_and_read_probe(request: Request):
            request.session["uid"] = 42
            return {"uid": get_current_uid(request)}

        client = make_full_probe_client(tmp_path, _set_and_read_probe)
        resp = client.get("/test/probe")
        assert resp.json()["uid"] == 42
        assert isinstance(resp.json()["uid"], int)


