"""Async SQLAlchemy engine and session helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from .base import Base

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


def normalize_async_db_url(db_url: str) -> str:
    """Ensure SQLite URLs use the async aiosqlite driver."""

    if db_url.startswith('sqlite+aiosqlite://'):
        return db_url
    if db_url.startswith('sqlite://'):
        return db_url.replace('sqlite://', 'sqlite+aiosqlite://', 1)
    return db_url


def create_engine(db_url: str) -> AsyncEngine:
    return create_async_engine(normalize_async_db_url(db_url), future=True)


def create_session_factory(db_url: str) -> async_sessionmaker[AsyncSession]:
    engine = create_engine(db_url)
    return async_sessionmaker(engine, expire_on_commit=False)


def _ensure_merge_profile_columns(sync_connection) -> None:
    inspector = inspect(sync_connection)
    columns = {column['name'] for column in inspector.get_columns('merge_profiles')}
    if 'composite_template_id' not in columns:
        sync_connection.exec_driver_sql('ALTER TABLE merge_profiles ADD COLUMN composite_template_id INTEGER')


async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.run_sync(_ensure_merge_profile_columns)

async def get_session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


__all__ = ['create_engine', 'create_session_factory', 'get_session', 'init_db', 'normalize_async_db_url']
