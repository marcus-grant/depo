# src/depo/web/app.py
"""
FastAPI application factory.

Wires dependencies from DepoConfig and registers routes.

Author: Marcus Grant
Created: 2026-02-09
License: Apache-2.0
"""

import sqlite3

from fastapi import FastAPI

from depo.cli.config import DepoConfig
from depo.repo.sqlite import SqliteRepository, init_db
from depo.service.ingest import IngestService
from depo.service.orchestrator import IngestOrchestrator
from depo.storage.filesystem import FilesystemStorage


def app_factory(config: DepoConfig) -> FastAPI:
    """Create and configure a FastAPI application.

    Stores config and wired dependencies in app.state.
    Includes route handlers via APIRouter.
    """
    # Start FastAPI lifecycle storing DepoConfig
    app = FastAPI()
    app.state.config = config

    # Initialize DB, create Repository, StorageBackend
    app.state.config.db_path.parent.mkdir(parents=True, exist_ok=True)
    app.state.config.store_root.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(app.state.config.db_path)
    init_db(conn)
    repo = SqliteRepository(conn)
    store = FilesystemStorage(root=app.state.config.store_root)
    service = IngestService()

    # Store server's repo, store & orchestrator instances
    app.state.repo, app.state.store = repo, store
    app.state.orchestrator = IngestOrchestrator(service, repo, store)

    # Dynamically import routes router
    from depo.web.routes import router

    # Store the router for FastAPI
    app.include_router(router)
    return app  # Return FastAPI app
