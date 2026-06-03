# tests/web/test_logging.py
"""
Integration tests for error logging through the web stack.
Author: Marcus Grant
Created: 2026-05-30
License: Apache-2.0
"""

import logging
from dataclasses import replace

import pytest

from depo.web import app
from tests.factories import make_config


class TestAppFactoryLogging:
    """app_factory configures the depo logger on startup."""

    def test_app_factory_configures_logging(self, tmp_path):
        """app_factory sets the depo logger to the configured level."""
        logger = logging.getLogger("depo")
        original = logger.level
        logger.setLevel(logging.WARNING)
        try:
            app.app_factory(replace(make_config(tmp_path), log_level="DEBUG"))
            assert logger.level == logging.DEBUG
        finally:
            logger.setLevel(original)


class TestErrorLoggingIntegration:
    """End-to-end logging behavior for expected errors."""

    def test_not_found_logs_info_record(self, t_client, caplog):
        """A 404 through the stack emits one INFO record carrying the code."""
        caplog.set_level(logging.INFO, logger="depo")
        t_client.get("/ZZZZZZZZ/info")

        def is_depo_info(r):
            return r.name.startswith("depo") and r.levelno == logging.INFO

        records = [r for r in caplog.records if is_depo_info(r)]
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
