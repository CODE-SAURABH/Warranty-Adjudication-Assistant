from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes.claims import router as claims_router
from .api.routes.health import router as health_router
from .api.routes.policy_corpus import router as policy_corpus_router
from .core.config import settings
from .db import ensure_database_ready


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_database_ready()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Production-style FastAPI backend for smart warranty adjudication.",
        lifespan=lifespan,
    )
    if settings.cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_allowed_origins),
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )
    app.include_router(health_router)
    app.include_router(claims_router)
    app.include_router(policy_corpus_router)
    return app


app = create_app()
