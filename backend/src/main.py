"""FastAPI application entrypoint.

Wires templates, static files, and routers. Feature routers (search, upload, images) are
added in later phases; Phase 0 ships the app skeleton, health check, and home page.
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src import __version__
from src.config import get_settings
from src.routes import health, home
from src.templating import STATIC_DIR

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.image_cache_dir.mkdir(parents=True, exist_ok=True)
    log.info("scryme.startup", version=__version__, environment=settings.environment)
    yield
    log.info("scryme.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="scryme", version=__version__, lifespan=lifespan)

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    app.include_router(health.router)
    app.include_router(home.router)

    # Cached card images are served from the data volume.
    settings.image_cache_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/images", StaticFiles(directory=settings.image_cache_dir), name="images")

    return app


app = create_app()
