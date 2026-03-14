"""FastAPI application wiring."""

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..db import create_engine, init_db, normalize_async_db_url
from .routes import api_router

WEBUI_DIST = Path(__file__).resolve().parent.parent / 'webui' / 'dist'


def _build_lifespan(db_url: str) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(db_url)
        session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(engine, expire_on_commit=False)
        app.state.db_url = db_url
        app.state.engine = engine
        app.state.session_factory = session_factory
        await init_db(engine)
        try:
            yield
        finally:
            await engine.dispose()

    return lifespan


def create_app(*, db_url: str | None = None) -> FastAPI:
    """Create the application instance."""

    normalized_db_url = normalize_async_db_url(db_url or 'sqlite+aiosqlite:///./clash_sub_manager.db')
    app = FastAPI(title='Clash Sub Manager', version='0.1.0', lifespan=_build_lifespan(normalized_db_url))
    app.include_router(api_router)
    if WEBUI_DIST.exists():
        app.mount('/ui', StaticFiles(directory=WEBUI_DIST, html=True), name='webui')
    return app


app = create_app()
