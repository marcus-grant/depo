# tests/web/test_deps.py
"""
Tests for FastAPI dependency providers.
Author: Marcus Grant
Created: 2026-06-29
License: Apache-2.0
"""

import pytest
from fastapi import Depends, Request
from starlette.testclient import TestClient

from depo.web.deps import require_auth
from tests.factories import make_config


class TestRequireAuth:
    """Tests for the require_auth dependency."""

    def _probe_request(self, path, probe_fn, **kwargs):
        """Fire a GET /_probe/response against a full-stack app and return
        the response. probe_fn is wired as the route handler, receiving
        injected dependencies. Extra kwargs forwarded to client.get.
        """
        from depo.web.app import app_factory

        app = app_factory(make_config(path))
        app.add_api_route("/_probe/response", probe_fn, methods=["GET"])
        client = TestClient(app)
        if "cookies" in kwargs:
            client.cookies.update(kwargs.pop("cookies"))
        return client.get("/_probe/response", **kwargs)

    @staticmethod
    def _auth_fn(uid: int = Depends(require_auth)):
        return {"uid": uid}

    def test_yields_uid_when_authenticated(self, tmp_path):
        """require_auth yields the session uid for an authenticated request."""

        def _set_session_fn(request: Request):
            request.session["uid"] = 42
            return {}

        resp = self._probe_request(tmp_path, _set_session_fn)
        cookie = resp.cookies["session"]

        resp = self._probe_request(tmp_path, self._auth_fn, cookies={"session": cookie})
        assert resp.json()["uid"] == 42

    @pytest.mark.skip("Unimplemented app-level AuthRequiredError handler")
    def test_raises_when_unauthenticated(self, tmp_path):
        """require_auth raises AuthRequiredError when no session uid is present."""

        resp = self._probe_request(tmp_path, self._auth_fn)
        assert resp.status_code == 401
