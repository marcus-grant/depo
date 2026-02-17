# tests/web/test_negotiate.py
"""
Tests for content negotiation.
Author: Marcus Grant
Created: 2026-02-12
License: Apache-2.0
"""

import pytest

from depo.web.negotiate import wants_html
from tests.factories.web import make_probe_client


class TestWantsHtml:
    """Accept header detection for browser vs API dispatch.

    Uses a minimal test app since no depo routes
    consume wants_html yet.
    """

    @pytest.mark.parametrize(
        "accept_value, expected",
        [
            ("text/html", True),
            ("text/html,application/json", True),
            ("application/json", False),
            ("*/*", False),
        ],
    )
    def test_true_for_accept_text_html(self, accept_value, expected):
        """Accept: text/html -> True (browser)"""
        client = make_probe_client(lambda r: {"html": wants_html(r)})
        headers = {"Accept": accept_value}
        assert client.get("/probe", headers=headers).json()["html"] == expected

    def test_no_accept_header_false(self):
        """Accept: text/html -> True (browser)"""
        client = make_probe_client(lambda r: {"html": wants_html(r)})
        assert not client.get("/probe").json()["html"]
