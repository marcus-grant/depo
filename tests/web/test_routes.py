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
from fastapi.testclient import TestClient

from depo.util import errors
from depo.util.password import hash_password
from tests.factories import HEADER_BROWSER, HEADER_HTMX
from tests.factories.db import insert_user
from tests.fixtures import KnownUser
from tests.helpers.assertions import assert_no_persistence


class TestRouteRegistration:
    """Fixed-path routes are not swallowed by /{code} wildcard."""

    def test_health_not_captured_by_wildcard(self, t_client):
        """GET /health returns 200 OK, not a shortcode lookup."""
        resp = t_client.get("/health")
        assert resp.status_code == 200
        assert resp.text == "ok"

    def test_upload_not_captured_by_wildcard(self, t_user: TestClient):
        """GET /upload returns upload page, not a shortcode lookup."""
        assert (resp := t_user.get("/upload")).status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_root_not_captured_by_wildcard(self, t_client):
        """GET / redirects to /upload, not a shortcode lookup."""
        assert (resp := t_client.get("/", follow_redirects=False)).status_code == 302
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
        assert errors.AuthenticationError.message in resp.text
        assert '"login__error"' in resp.text
        assert "session" not in resp.cookies

    def test_get_login_renders_form(self, t_browser):
        """GET /login returns 200 with the login form."""
        resp = t_browser.get("/login")
        self._assert_login_form(resp)
        assert resp.status_code == 200
        assert "session" not in resp.cookies

    def test_get_login_authenticated_redirects(self, t_known_user: KnownUser):
        """GET /login while authenticated redirects to / instead of rendering."""
        data = {"email": t_known_user.user.email, "password": t_known_user.password}
        t_known_user.client.post("/login", data=data, follow_redirects=False)
        resp = t_known_user.client.get("/login", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers.get("location") == "/"

    def test_post_valid_credentials_redirects(self, t_known_user: KnownUser):
        """POST /login with valid credentials 302s and sets session uid."""
        data = {"email": t_known_user.user.email, "password": t_known_user.password}
        resp = t_known_user.client.post("/login", data=data, follow_redirects=False)
        assert resp.status_code == 302
        assert "session" in resp.cookies

    def test_post_wrong_password_rerenders_form(self, t_known_user: KnownUser):
        """POST /login with wrong password re-renders the form with an error."""
        data = {"email": t_known_user.user.email, "password": "wrong-pass"}
        resp = t_known_user.client.post("/login", data=data, follow_redirects=False)
        self._assert_login_rejected(resp)

    def test_post_unknown_email_rerenders_form(self, t_known_user: KnownUser):
        """POST /login with unknown email re-renders the form with an error."""
        data = {"email": "not-an@email.com", "password": t_known_user.password}
        resp = t_known_user.client.post("/login", data=data, follow_redirects=False)
        self._assert_login_rejected(resp)


class TestLogoutRoute:
    """Tests for GET /logout."""

    def test_logout_clears_session_and_redirects(self, t_known_user: KnownUser):
        """GET /logout clears the session, subsequent request is unauthenticated."""
        data = {"email": t_known_user.user.email, "password": t_known_user.password}
        t_known_user.client.post("/login", data=data, follow_redirects=False)
        resp = t_known_user.client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302
        assert "session" not in resp.cookies
        assert (
            "session"
            not in t_known_user.client.get("/", follow_redirects=False).cookies
        )


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
        assert errors.AuthenticationError.message in resp.text

    def test_logout_clears_session(self, t_client):
        """GET /logout 302s and clears the session cookie."""
        mail, pw = self._seed_user(t_client)
        data = {"email": mail, "password": pw}
        t_client.post("/login", data=data, follow_redirects=False)
        resp = t_client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302
        assert "session" not in resp.cookies


class TestUploadGate:
    """Integration gate for authenticated-only upload routes."""

    def test_unauth_post_upload_rejected(self, t_client):
        """Unauthenticated POST /upload returns 401 and creates no item."""
        resp = t_client.post("/upload", files={"file": ("t.txt", b"hHello!")})
        assert resp.status_code == 401
        assert errors.AuthRequiredError.message in resp.text
        assert_no_persistence(cast(FastAPI, t_client.app))

    def test_unauth_get_upload_form_rejected(self, t_browser):
        """Unauthenticated GET /upload returns 401 and does not render the form."""
        resp, login = t_browser.get("/upload"), 'a[href="/login"]'
        assert resp.status_code == 401
        assert errors.AuthRequiredError.message in resp.text
        assert BSoup(resp.text, "html.parser").select_one(login) is not None

    def test_htmx_rejection_carries_login_link(self, t_client: TestClient):
        """The htmx upload-rejection partial carries a login link."""
        data = {"content": "hello", "format": "txt"}
        resp = t_client.post("/upload", data=data, headers=HEADER_HTMX)
        assert resp.status_code == 200
        assert errors.AuthRequiredError.message in resp.text
        assert BSoup(resp.text, "html.parser").select_one('a[href="/login"]')
        assert "<!-- BEGIN: errors/partial.html -->" in resp.text

    def test_browser_rejection_carries_login_link(self, t_client: TestClient):
        """The browser upload-rejection surface carries a login link."""
        data = {"content": "hello", "format": "txt"}
        resp = t_client.post("/upload", data=data, headers=HEADER_BROWSER)
        assert resp.status_code == 401
        assert errors.AuthRequiredError.message in resp.text
        assert "BEGIN: errors/page.html#content" in resp.text
        assert "<!-- BEGIN: errors/partial.html -->" not in resp.text
        assert BSoup(resp.text, "html.parser").select_one('a[href="/login"]')

    def test_known_user_post_upload_creates_item_with_uid(
        self, t_known_user: KnownUser
    ):
        """An authenticated POST /upload creates an item with the session uid."""
        data = {"email": t_known_user.user.email, "password": t_known_user.password}
        t_known_user.client.post("/login", data=data, follow_redirects=False)
        resp = t_known_user.client.post("/upload", files={"file": ("t.txt", b"Hello!")})
        code = resp.headers.get("X-Depo-Code")
        assert resp.status_code == 201
        assert code is not None
        conn = cast(FastAPI, t_known_user.client.app).state.repo._conn
        row = conn.execute("SELECT uid FROM items WHERE code = ?", (code,)).fetchone()
        assert row["uid"] == t_known_user.user.id

    def test_known_user_get_upload_renders_form(self, t_user: TestClient):
        """An authenticated GET /upload renders the form."""
        assert (resp := t_user.get("/upload")).status_code == 200
        assert "<!-- BEGIN: upload/page.html" in resp.text
