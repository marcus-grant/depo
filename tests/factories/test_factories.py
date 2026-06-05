# tests/factories/test_factories.py
"""
Tests for the test factories.
Exercises the reusable builders in tests/factories,
starting with make_config keyword overrides.
Author: Marcus Grant
Created: 2026-06-04
License: Apache-2.0
"""

from pathlib import Path

from tests.factories import make_config


class TestMakeConfig:
    """Tests for the make_config factory."""

    def test_override_reaches_config(self, tmp_path: Path) -> None:
        """An applied keyword override lands on the returned config."""
        assert make_config(tmp_path, max_size_bytes=1).max_size_bytes == 1
        assert make_config(tmp_path, log_level="INFO").log_level == "INFO"
