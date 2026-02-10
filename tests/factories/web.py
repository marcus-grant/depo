# tests/factories/web.py
"""
Web layer test helpers.

Builds configured TestClient instances for integration
tests against the FastAPI application.

Author: Marcus Grant
Created: 2026-02-09
License: Apache-2.0
"""

from pathlib import Path

from fastapi.testclient import TestClient

from depo.web.app import app_factory
from tests.factories.config import make_config


def make_client(p: Path) -> TestClient:
    """Build a TestClient from a DepoConfig pointing at tmp_path."""
    return TestClient(app_factory(make_config(p)))
