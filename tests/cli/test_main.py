# tests/cli/test_main.py
"""
Tests for CLI commands.

Author: Marcus Grant
Created: 2026-02-09
License: Apache-2.0
"""

import pytest
from click.testing import CliRunner

from depo.cli.main import cli


class TestInit:
    """Tests for `depo init`."""

    # - creates db_path parent directory
    # - creates store_root directory
    # - idempotent (succeeds when dirs already exist)
    # - initializes database schema (depo.db created)
