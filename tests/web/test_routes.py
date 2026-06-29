# tests/web/test_routes.py
"""
Tests for top-level route wiring.
Covers root redirect, health probe, and route aliases
registered in the routes package init.
Author: Marcus Grant
Created: 2026-02-23
License: Apache-2.0
"""

from typing import cast

from bs4 import BeautifulSoup as BSoup
from fastapi import FastAPI

from depo.util.errors import AuthenticationError
from depo.util.password import hash_password
from tests.factories.db import insert_user


class TestRouteRegistration:
    """Fixed-path routes are not swallowed by /{code} wildcard."""

    def test_health_not_captured_by_wildcard(self, t_client):
        """GET /health returns 200 OK, not a shortcode lookup."""
        resp = t_client.get("/health")
        assert resp.status_code == 200
        assert resp.text == "ok"

    def test_upload_not_captured_by_wildcard(self, t_client):
        """GET /upload returns upload page, not a shortcode lookup."""
        resp = t_client.get("/upload")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_root_not_captured_by_wildcard(self, t_client):
        """GET / redirects to /upload, not a shortcode lookup."""
        resp = t_client.get("/", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/upload"

    def test_wildcard_does_not_shadow_fixed_routes(self, t_client):
        """Every fixed-path GET route resolves without hitting /{code}."""
        app = t_client.app
        fixed_gets = [
            r.path
            for r in app.routes
            if hasattr(r, "methods") and "GET" in r.methods and "{" not in r.path
        ]
        for path in fixed_gets:
            resp = t_client.get(path, follow_redirects=False)
            assert resp.status_code != 404, f"{path} shadowed by wildcard"


class TestRootRedirect:
    """GET / redirects to /upload.

    # Returns redirect status
    # Redirects to /upload
    """

    def test_redirects_to_upload_302(self, t_client):
        """GET / redirects with 302 to /upload"""
        resp = t_client.get(url="/", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers.get("location") == "/upload"


class TestLoginRoute:
    """Tests for GET and POST /login."""

    def _assert_login_form(self, resp):
        """Assert the response is an HTML page containing a valid login form."""
        assert "text/html" in resp.headers["content-type"]
        form = BSoup(resp.text, "html.parser").select_one("form.login__form")
        assert form is not None
        assert str(form.get("method", "")).lower() == "post"
        assert form.select_one("input[type='email']") is not None
        assert form.select_one("input[type='password']") is not None
        assert form.select_one("button[type='submit']") is not None

    def _assert_login_rejected(self, resp):
        """Assert the response is a rejected login: form re-rendered with a
        generic error, 401 status, and no session established."""
        self._assert_login_form(resp)
        assert resp.status_code == 401
        assert AuthenticationError.message in resp.text
        assert '"login__error"' in resp.text
        assert "session" not in resp.cookies

    def test_get_login_renders_form(self, t_browser):
        """GET /login returns 200 with the login form."""
        resp = t_browser.get("/login")
        self._assert_login_form(resp)
        assert resp.status_code == 200
        assert "session" not in resp.cookies

    def test_get_login_authenticated_redirects(self, t_authed):
        """GET /login while authenticated redirects to / instead of rendering."""
        data = {"email": t_authed.user.email, "password": t_authed.password}
        t_authed.client.post("/login", data=data, follow_redirects=False)
        resp = t_authed.client.get("/login", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers.get("location") == "/"

    def test_post_valid_credentials_redirects(self, t_authed):
        """POST /login with valid credentials 302s and sets session uid."""
        data = {"email": t_authed.user.email, "password": t_authed.password}
        resp = t_authed.client.post("/login", data=data, follow_redirects=False)
        assert resp.status_code == 302
        assert "session" in resp.cookies

    def test_post_wrong_password_rerenders_form(self, t_authed):
        """POST /login with wrong password re-renders the form with an error."""
        data = {"email": t_authed.user.email, "password": "wrong-pass"}
        resp = t_authed.client.post("/login", data=data, follow_redirects=False)
        self._assert_login_rejected(resp)

    def test_post_unknown_email_rerenders_form(self, t_authed):
        """POST /login with unknown email re-renders the form with an error."""
        data = {"email": "not-an@email.com", "password": t_authed.password}
        resp = t_authed.client.post("/login", data=data, follow_redirects=False)
        self._assert_login_rejected(resp)


class TestLogoutRoute:
    """Tests for GET /logout."""

    def test_logout_clears_session_and_redirects(self, t_authed):
        """GET /logout clears the session, subsequent request is unauthenticated."""
        data = {"email": t_authed.user.email, "password": t_authed.password}
        t_authed.client.post("/login", data=data, follow_redirects=False)
        resp = t_authed.client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302
        assert "session" not in resp.cookies
        assert "session" not in t_authed.client.get("/", follow_redirects=False).cookies


class TestLoginSession:
    """End-to-end login, session, and logout over HTTP.

    Probes the session lifecycle via the t_client cookie jar; no
    authenticated-only route exists until ft/upload-gate, so value-level
    uid recognition is left to the get_current_uid unit test.
    """

    def _seed_user(self, t_client):
        """Seed a test user with a known password into the client's db.
        Returns (mail, pw) for use in login form data."""
        conn = cast(FastAPI, t_client.app).state.repo._conn
        mail, pw = "guy@example.com", "test-password"
        insert_user(conn, email=mail, pw_hash=hash_password(pw, n=2, r=1, p=1))
        return mail, pw

    def test_valid_login_starts_session(self, t_client):
        """POST /login with valid creds 302s and sets a session cookie."""
        mail, pw = self._seed_user(t_client)
        data = {"email": mail, "password": pw}
        resp = t_client.post("/login", data=data, follow_redirects=False)
        assert resp.status_code == 302
        assert "session" in resp.cookies

    def test_bad_credentials_rejected(self, t_client):
        """POST /login with a wrong password re-renders the form, no session."""
        mail, _ = self._seed_user(t_client)
        data = {"email": mail, "password": "bad-password"}
        resp = t_client.post("/login", data=data, follow_redirects=False)
        assert resp.status_code == 401
        assert "session" not in resp.cookies
        assert AuthenticationError.message in resp.text

    def test_logout_clears_session(self, t_client):
        """GET /logout 302s and clears the session cookie."""
        mail, pw = self._seed_user(t_client)
        data = {"email": mail, "password": pw}
        t_client.post("/login", data=data, follow_redirects=False)
        resp = t_client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302
        assert "session" not in resp.cookies
