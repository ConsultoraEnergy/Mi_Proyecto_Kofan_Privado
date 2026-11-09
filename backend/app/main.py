"""
Punto de entrada de la API de Hotel Kawari.

    uvicorn backend.app.main:app --reload
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.v1.router import api_router
from backend.app.core.errors import register_exception_handlers
from backend.app.core.settings import get_settings
from backend.app.db import client as mongo
from backend.app.db.indexes import ensure_database
from backend.app.modules.cms.service import ensure_defaults
from backend.app.workers.scheduler import start_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    db = await mongo.connect(settings)
    await ensure_database(db)
    await ensure_defaults()
    scheduler = start_scheduler(settings)
    try:
        yield
    finally:
        if scheduler:
            scheduler.shutdown(wait=False)
        await mongo.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=f"{settings.hotel_name} API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )
    register_exception_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,  # necesario para la cookie del refresh token
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # Solo fotos públicas. Los comprobantes viven en private_upload_dir y NO se montan (5.6).
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.private_upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

    app.include_router(api_router)
    return app


app = create_app()
