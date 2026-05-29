# tests/web/test_error_responses.py
"""
Tests for web layer error response builders.
Author: Marcus Grant
Created: 2026-03-12
Revised: 2026-05-05
License: Apache-2.0
"""

from depo.util.errors import DepoError, NotFoundError
from depo.web import error as web_errs
from tests.factories import make_request


class TestApiError:
    """Tests for api_error response builder."""

    def test_status_from_error(self):
        """Response status matches e.status."""
        e = NotFoundError("ABC12345")
        resp = web_errs.api_error(e)
        assert resp.status_code == 404

    def test_body_is_error_message(self):
        """Response body is str(e)."""
        e = NotFoundError("ABC12345")
        resp = web_errs.api_error(e)
        assert b"ABC12345" in resp.body


class TestHtmxError:
    """Tests for htmx_error kwargs builder."""

    def test_returns_error_partial(self):
        """Returns dict with errors/partial.html template name."""
        e = DepoError("something went wrong")
        assert web_errs.htmx_error(e)["name"] == "errors/partial.html"

    def test_context_contains_error_object(self):
        """Context contains error object, not string."""
        e = DepoError("something went wrong")
        assert web_errs.htmx_error(e)["context"]["error"] is e

    def test_default_role_is_alert(self):
        """Default role 'alert' passed in context."""
        e = DepoError("something went wrong")
        assert web_errs.htmx_error(e)["context"]["role"] == "alert"

    def test_custom_role_in_context(self):
        """Custom role passed through to context."""
        e = DepoError("something went wrong")
        assert web_errs.htmx_error(e, role="status")["context"]["role"] == "status"


class TestBrowserError:
    """Tests for browser_error TemplateResponse builder."""

    def test_uses_page_template(self):
        """browser_error always uses errors/page.html."""
        req = make_request()
        e = NotFoundError("ABC12345")
        resp = web_errs.browser_error(req, e)
        assert resp.template.name == "errors/page.html"  # type: ignore

    def test_status_code_from_error(self):
        """Response status code matches error status."""
        req = make_request()
        e = NotFoundError("ABC12345")
        assert web_errs.browser_error(req, e).status_code == 404

    def test_context_contains_error_object(self):
        """Context contains error object."""
        req = make_request()
        e = NotFoundError("ABC12345")
        assert web_errs.browser_error(req, e).context["error"] is e  # type: ignore

    def test_context_contains_issues_url(self):
        """Context contains issues URL."""
        req = make_request()
        e = NotFoundError("ABC12345")
        resp = web_errs.browser_error(req, e)
        assert resp.context["issues_url"] == web_errs._ISSUES_URL  # type: ignore
