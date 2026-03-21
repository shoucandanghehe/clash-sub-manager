"""FastAPI application wiring."""

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .. import __version__
from ..db import create_engine, default_db_url, init_db, normalize_async_db_url
from .routes import api_router

WEBUI_STATIC = Path(__file__).resolve().parent.parent / 'static' / 'webui'
WEBUI_DEV_DIST = Path(__file__).resolve().parents[3] / 'webui' / 'dist'


def _resolve_webui_dir() -> Path | None:
    """Prefer packaged assets, but fall back to a local frontend build during development."""

    for candidate in (WEBUI_STATIC, WEBUI_DEV_DIST):
        if (candidate / 'index.html').is_file():
            return candidate
    return None


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

    normalized_db_url = normalize_async_db_url(db_url or default_db_url())
    app = FastAPI(title='Clash Sub Manager', version=__version__, lifespan=_build_lifespan(normalized_db_url))
    app.include_router(api_router)
    webui_dir = _resolve_webui_dir()
    if webui_dir is not None:
        app.mount('/ui', StaticFiles(directory=webui_dir, html=True), name='webui')
    return app


app = create_app()
