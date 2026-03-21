"""Async SQLAlchemy engine and session helpers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from platformdirs import user_data_path
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from .base import Base

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


APP_DATA_DIR_NAME = 'clash-sub-manager'
DEFAULT_DB_FILENAME = 'clash_sub_manager.db'


def default_db_path() -> Path:
    """Return the user-specific application data path for the SQLite database."""

    return user_data_path(appname=APP_DATA_DIR_NAME, appauthor=False, ensure_exists=True) / DEFAULT_DB_FILENAME


def default_db_url() -> str:
    """Return the default SQLite URL stored under the user application data directory."""

    return f'sqlite+aiosqlite:///{default_db_path()}'


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


def _drop_subscription_template_column(sync_connection) -> None:
    inspector = inspect(sync_connection)
    columns = {column['name'] for column in inspector.get_columns('subscriptions')}
    if 'template_id' not in columns:
        return

    sync_connection.exec_driver_sql('PRAGMA foreign_keys=OFF')
    try:
        sync_connection.exec_driver_sql(
            """
            CREATE TABLE subscriptions__new (
                id INTEGER PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                url VARCHAR(2048),
                content TEXT,
                proxy VARCHAR(2048),
                headers JSON NOT NULL,
                follow_redirects BOOLEAN NOT NULL,
                enabled BOOLEAN NOT NULL
            )
            """
        )
        sync_connection.exec_driver_sql(
            """
            INSERT INTO subscriptions__new (
                id, name, url, content, proxy, headers, follow_redirects, enabled
            )
            SELECT
                id, name, url, content, proxy, headers, follow_redirects, enabled
            FROM subscriptions
            """
        )
        sync_connection.exec_driver_sql('DROP TABLE subscriptions')
        sync_connection.exec_driver_sql('ALTER TABLE subscriptions__new RENAME TO subscriptions')
    finally:
        sync_connection.exec_driver_sql('PRAGMA foreign_keys=ON')


async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.run_sync(_ensure_merge_profile_columns)
        await connection.run_sync(_drop_subscription_template_column)


async def get_session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


__all__ = [
    'APP_DATA_DIR_NAME',
    'DEFAULT_DB_FILENAME',
    'create_engine',
    'create_session_factory',
    'default_db_path',
    'default_db_url',
    'get_session',
    'init_db',
    'normalize_async_db_url',
]
