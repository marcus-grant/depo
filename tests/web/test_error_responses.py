# tests/web/test_error_responses.py
"""
Tests for web layer error response builders.
Author: Marcus Grant
Created: 2026-03-12
Revised: [2026-05-05, 2026-06-03]
License: Apache-2.0
"""

import logging

import pytest

from depo.util.errors import DepoError, NotFoundError
from depo.web.error import _ISSUES_URL, api_error, browser_error, htmx_error, log_error
from tests.factories import make_request

_T_DEPO_ERR = DepoError("something went wrong")
_T_NOTFOUND_ERR = NotFoundError(id="ABC12345")


class TestApiError:
    """Tests for api_error response builder."""

    def test_status_from_error(self):
        """Response status matches e.status."""
        assert api_error(_T_NOTFOUND_ERR).status_code == 404

    def test_body_is_error_message(self):
        """Response body is str(e)."""
        assert b"ABC12345" in api_error(_T_NOTFOUND_ERR).body


class TestHtmxError:
    """Tests for htmx_error kwargs builder."""

    def test_returns_error_partial(self):
        """Returns dict with errors/partial.html template name."""
        assert htmx_error(_T_DEPO_ERR)["name"] == "errors/partial.html"

    def test_context_contains_error_object(self):
        """Context contains error object, not string."""
        assert htmx_error(_T_DEPO_ERR)["context"]["error"] is _T_DEPO_ERR

    def test_default_role_is_alert(self):
        """Default role 'alert' passed in context."""
        assert htmx_error(_T_DEPO_ERR)["context"]["role"] == "alert"

    def test_custom_role_in_context(self):
        """Custom role passed through to context."""
        assert htmx_error(_T_DEPO_ERR, role="status")["context"]["role"] == "status"


class TestBrowserError:
    """Tests for browser_error TemplateResponse builder."""

    def test_uses_page_template(self):
        """browser_error always uses errors/page.html."""
        req, e = make_request(), _T_NOTFOUND_ERR
        assert browser_error(req, e).template.name == "errors/page.html"  # type: ignore

    def test_status_code_from_error(self):
        """Response status code matches error status."""
        e = _T_NOTFOUND_ERR
        assert browser_error(make_request(), e).status_code == 404

    def test_context_contains_error_object(self):
        """Context contains error object."""
        e = _T_NOTFOUND_ERR
        assert browser_error(make_request(), e).context["error"] is e  # type: ignore

    def test_context_contains_issues_url(self):
        """Context contains issues URL."""
        resp = browser_error(make_request(), _T_NOTFOUND_ERR)
        assert resp.context["issues_url"] == _ISSUES_URL  # type: ignore


class TestErrorLogging:
    """Builders emit one depo log record at the error's severity."""

    def test_log_error_emits_one_record_at_severity(self, caplog):
        """log_error emits exactly one depo record at the error's severity."""
        caplog.set_level(logging.DEBUG, logger="depo")
        log_error(_T_NOTFOUND_ERR)
        recs = [r for r in caplog.records if r.name.startswith("depo")]
        assert len(recs) == 1
        assert recs[0].levelno == logging.INFO
        assert recs[0].getMessage() == _T_NOTFOUND_ERR.message

    def test_log_error_attaches_exc_info(self, caplog):
        """log_error attaches exc_info from the error's exception."""
        caplog.set_level(logging.DEBUG, logger="depo")
        err = NotFoundError(id="ABC12345")
        err.exception = ValueError("boom")
        log_error(err)
        recs = [r for r in caplog.records if r.name.startswith("depo")]
        assert recs[0].exc_info is not None

    @pytest.mark.parametrize(
        "call",
        [
            lambda e: api_error(e),
            lambda e: browser_error(make_request(), e),
            lambda e: htmx_error(e),
        ],
        ids=["api", "browser", "htmx"],
    )
    def test_builder_logs_message_at_severity(self, caplog, call):
        """Each builder logs one depo record at the error's severity."""
        caplog.set_level(logging.DEBUG, logger="depo")
        call(_T_NOTFOUND_ERR)
        recs = [r for r in caplog.records if r.name.startswith("depo")]
        assert len(recs) == 1
        assert recs[0].levelno == logging.INFO
        assert recs[0].getMessage() == _T_NOTFOUND_ERR.message

    def test_logs_exc_info_when_exception_set(self, caplog):
        """exc_info is attached when the error wraps an exception."""
        caplog.set_level(logging.DEBUG, logger="depo")
        err = NotFoundError(id="ABC12345")
        err.exception = ValueError("boom")
        api_error(err)
        recs = [r for r in caplog.records if r.name.startswith("depo")]
        assert recs[0].exc_info is not None
