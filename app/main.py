from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import build_router
from app.config import Settings
from app.db import build_session_factory, create_tables, get_db_session
from app.service import TransformationCacheService
from app.transformer import Transformer


def create_app(settings: Settings | None = None, transformer: Transformer | None = None) -> FastAPI:
    settings = settings or Settings()
    engine, session_factory = build_session_factory(settings)
    cache_service = TransformationCacheService(transformer or Transformer())

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        create_tables(engine)
        yield
        engine.dispose()

    app = FastAPI(
        title="Payload Cache Service",
        version="0.1.0",
        description="Caches transformation results and deduplicates generated payloads.",
        lifespan=lifespan,
    )

    def get_db():
        yield from get_db_session(session_factory)

    app.include_router(build_router(cache_service, get_db))

    @app.get("/health", include_in_schema=False)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
