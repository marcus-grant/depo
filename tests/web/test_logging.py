# tests/web/test_logging.py
"""
Integration tests for error logging through the web stack.
Author: Marcus Grant
Created: 2026-05-30
License: Apache-2.0
"""

import logging

import pytest

from depo.web import app


class TestErrorLoggingIntegration:
    """End-to-end logging behavior for expected errors."""

    @pytest.mark.skip("logging not implemented")
    def test_not_found_logs_info_record(self, t_client, caplog):
        """A 404 through the stack emits one INFO record carrying the code."""
        caplog.set_level(logging.INFO, logger="depo")
        t_client.get("/ZZZZZZZZ/info")
        records = [r for r in caplog.records if r.levelno == logging.INFO]
        assert len(records) == 1
        assert "ZZZZZZZZ" in records[0].getMessage()


class TestConfigureLogging:
    """Tests for configure_logging level mapping."""

    @pytest.mark.parametrize(
        "name, level",
        [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
        ],
    )
    def test_sets_depo_logger_level(self, name, level):
        """configure_logging sets the depo logger to the named level."""
        logger = logging.getLogger("depo")
        original = logger.level
        try:
            app.configure_logging(name)
            assert logger.level == level
        finally:
            logger.setLevel(original)
