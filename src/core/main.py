"""FastAPI application: Neo4j driver lifecycle, API router, static web UI."""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from neo4j import AsyncGraphDatabase

from . import config
from .api import router
from .repository import Repository

log = logging.getLogger("core")


def create_app(cfg: config.Config) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        driver = AsyncGraphDatabase.driver(
            cfg.neo4j_uri,
            auth=(cfg.neo4j_user, cfg.neo4j_password),
            notifications_min_severity="WARNING",
        )
        await driver.verify_connectivity()
        app.state.driver = driver
        app.state.repo = Repository(driver)
        await app.state.repo.ensure_constraints()
        log.info("cbx-core ready on http://%s:%s (neo4j %s)", cfg.host, cfg.port, cfg.neo4j_uri)
        yield
        await driver.close()

    # Swagger UI under /api like everything else the API serves; "try it out" runs
    # against this instance.
    app = FastAPI(
        title="CBX Core",
        description="Provider-neutral infrastructure inventory graph: nodes, edges, schema.",
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
    )
    app.include_router(router)
    if cfg.webui_dir.is_dir():
        app.mount("/", StaticFiles(directory=cfg.webui_dir, html=True), name="webui")
    return app


def cli() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    cfg = config.load()
    uvicorn.run(create_app(cfg), host=cfg.host, port=cfg.port, log_level="info")
