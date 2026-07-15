# tests/web/test_deps.py
"""
Tests for FastAPI dependency providers.
Author: Marcus Grant
Created: 2026-06-29
License: Apache-2.0
"""

from fastapi import Depends, Request

from depo.web.deps import require_auth
from tests.factories import make_full_probe_client


class TestRequireAuth:
    """Tests for the require_auth dependency."""

    @staticmethod
    def _auth_fn(uid: int = Depends(require_auth)):
        return {"uid": uid}

    def test_yields_uid_when_authenticated(self, tmp_path):
        """require_auth yields the session uid for an authenticated request."""

        def _set_session_fn(request: Request):
            request.session["uid"] = 42
            return {}

        client = make_full_probe_client(tmp_path, _set_session_fn)
        cookie = client.get("/test/probe").cookies["session"]
        client = make_full_probe_client(tmp_path, self._auth_fn)
        client.cookies.set("session", cookie)
        resp = client.get("/test/probe")
        assert resp.json()["uid"] == 42

    def test_raises_when_unauthenticated(self, tmp_path):
        """require_auth raises AuthRequiredError when no session uid is present."""
        client = make_full_probe_client(tmp_path, self._auth_fn)
        assert client.get("/test/probe").status_code == 401
