# src/depo/web/deps.py
"""
FastAPI dependency providers.

Thin functions that pull wired dependencies from
app.state for injection via Depends().

Author: Marcus Grant
Created: 2026-02-09
License: Apache-2.0
"""

from fastapi import Request

from depo.repo.sqlite import SqliteRepository
from depo.service.orchestrator import IngestOrchestrator
from depo.storage.protocol import StorageBackend


def get_repo(request: Request) -> SqliteRepository:
    """Provide the SqliteRepository from app state."""
    return request.app.state.repo


def get_storage(request: Request) -> StorageBackend:
    """Provide the StorageBackend from app state."""
    return request.app.state.store


def get_orchestrator(request: Request) -> IngestOrchestrator:
    """Provide the IngestOrchestrator from app state."""
    return request.app.state.orchestrator
