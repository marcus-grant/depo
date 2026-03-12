# tests/web/test_error_responses.py
"""
Tests for web layer error response builders.
Author: Marcus Grant
Created: 2026-03-12
License: Apache-2.0
"""

from unittest.mock import MagicMock

from starlette.requests import Request

from depo.util.errors import DepoError, NotFoundError, ServerError
from depo.web import error as web_errs


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
        """Returns dict with error partial template name."""
        e = DepoError("something went wrong")
        result = web_errs.htmx_error(e)
        assert result["name"] == "partials/error.html"

    def test_context_contains_error_message(self):
        """Context dict contains error message string."""
        e = DepoError("something went wrong")
        result = web_errs.htmx_error(e)
        assert "something went wrong" in result["context"]["error"]


def make_mock_request(path: str = "/test") -> Request:
    mock = MagicMock(spec=Request)
    mock.url.path = path
    mock.method = "GET"
    return mock


class TestBrowserError:
    """Tests for browser_error TemplateResponse builder."""

    def test_404_uses_404_template(self):
        """NotFoundError returns 404 status and uses errors/404.html."""
        req = make_mock_request()
        e = NotFoundError("ABC12345")
        resp = web_errs.browser_error(req, e)
        assert resp.status_code == 404
        assert "404" in resp.template.name  # type: ignore

    def test_404_context_contains_id(self):
        """404 context includes the item id."""
        req = make_mock_request()
        e = NotFoundError("ABC12345")
        resp = web_errs.browser_error(req, e)
        assert "ABC12345" in resp.context["code"]  # type: ignore

    def test_500_uses_500_template(self):
        """ServerError returns 500 status and uses errors/500.html."""
        req = make_mock_request("/broken")
        e = ServerError()
        resp = web_errs.browser_error(req, e)
        assert resp.status_code == 500
        assert "500" in resp.template.name  # type: ignore

    def test_500_context_contains_path(self):
        """500 context includes request path."""
        req = make_mock_request("/broken")
        e = ServerError()
        resp = web_errs.browser_error(req, e)
        assert "/broken" in resp.context["path"]  # type: ignore
