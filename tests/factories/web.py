# tests/factories/web.py
"""
Web layer test helpers.

Builds configured TestClient instances for integration
tests against the FastAPI application.

Author: Marcus Grant
Created: 2026-02-09
License: Apache-2.0
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from depo.web.app import app_factory
from tests.factories.config import make_config


def make_client(p: Path) -> TestClient:
    """Build a TestClient from a DepoConfig pointing at tmp_path."""
    return TestClient(app_factory(make_config(p)))


def make_probe_client(probe_fn: Callable[[Request], Any]) -> TestClient:
    """Build a minimal test app with a single GET /probe route.
    probe_fn receives the Request, its return value becomes the response.
    """
    app = FastAPI()

    @app.get("/probe")
    def _probe(request: Request):
        return probe_fn(request)

    _ = _probe  # satisfy linters

    return TestClient(app)
