"""Async SQLAlchemy engine and session helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

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


async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def get_session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


__all__ = ['create_engine', 'create_session_factory', 'get_session', 'init_db', 'normalize_async_db_url']
