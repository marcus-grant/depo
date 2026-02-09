# src/depo/web/app.py
"""
FastAPI application factory.

Wires dependencies from DepoConfig and registers routes.

Author: Marcus Grant
Created: 2026-02-09
License: Apache-2.0
"""

from fastapi import FastAPI

from depo.cli.config import DepoConfig


def app_factory(config: DepoConfig) -> FastAPI:
    """Create and configure a FastAPI application.

    Stores config and wired dependencies in app.state.
    Includes route handlers via APIRouter.
    """
    # Start FastAPI lifecycle storing DepoConfig
    app = FastAPI()
    app.state.config = config
    # Dynamically import routes router
    from depo.web.routes import router

    # Store the router for FastAPI
    app.include_router(router)
    return app  # Return FastAPI app
