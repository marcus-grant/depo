# src/depo/web/app.py
"""
FastAPI application factory.

Wires dependencies from DepoConfig and registers routes.

Author: Marcus Grant
Created: 2026-02-09
License: Apache-2.0
"""

import logging
import sqlite3
from pathlib import Path

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

from depo.cli.config import DepoConfig
from depo.repo.sqlite import SqliteRepository, init_db
from depo.service.ingest import IngestService
from depo.service.orchestrator import IngestOrchestrator
from depo.storage.filesystem import FilesystemStorage
from depo.util.errors import AuthRequiredError, Severity
from depo.web.error import auth_required


def app_factory(config: DepoConfig) -> FastAPI:
    """Create and configure a FastAPI application.

    Stores config and wired dependencies in app.state.
    Includes route handlers via APIRouter.
    """
    # Configure the logger
    configure_logging(config.log_level)

    # Start FastAPI lifecycle storing DepoConfig
    app = FastAPI()
    app.state.config = config

    # Add middleware here
    app.add_middleware(
        SessionMiddleware,
        secret_key=config.session_secret,
        https_only=config.session_https_only,
        same_site="lax",
    )

    # Initialize DB, create Repository, StorageBackend
    app.state.config.db_path.parent.mkdir(parents=True, exist_ok=True)
    app.state.config.store_root.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(app.state.config.db_path, check_same_thread=False)
    init_db(conn)  # NOTE: Thread pooling/write queing in repo is not ready yet
    repo = SqliteRepository(conn)
    store = FilesystemStorage(root=app.state.config.store_root)
    service = IngestService(
        min_code_len=app.state.config.min_code_len,
        max_size_bytes=app.state.config.max_size_bytes,
        max_url_len=app.state.config.max_url_len,
    )

    # Store server's repo, store & orchestrator instances
    app.state.repo, app.state.store = repo, store
    app.state.orchestrator = IngestOrchestrator(service, repo, store)

    # Dynamically import routes router
    from depo.web.routes import router

    # Store the router for FastAPI
    app.include_router(router)

    # App-level boundary: catch non-DepoError exceptions that escape
    # per-route handlers, negotiate surface, delegate to a builder.
    from depo.web.error import unhandled

    app.add_exception_handler(Exception, unhandled)
    app.add_exception_handler(AuthRequiredError, auth_required)

    # Mount static assets directory for frontend - must come AFTER routes
    static_dir = Path(__file__).parent.parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    return app  # Return FastAPI app


def configure_logging(level: Severity) -> None:
    """Set the depo logger to the named level with a text handler"""
    logger = logging.getLogger("depo")
    logger.setLevel(level)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler()
        fmt = "%(levelname)s %(name)s: %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
