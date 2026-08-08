"""Async SQLAlchemy engine and session helpers."""

from collections.abc import AsyncIterator
from pathlib import Path
from uuid import UUID, uuid4

from platformdirs import user_data_path
from sqlalchemy import inspect
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from .base import Base

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


def _ensure_merge_profile_columns(sync_connection: Connection) -> None:
    inspector = inspect(sync_connection)
    columns = {column['name'] for column in inspector.get_columns('merge_profiles')}
    if 'composite_template_id' not in columns:
        sync_connection.exec_driver_sql('ALTER TABLE merge_profiles ADD COLUMN composite_template_id INTEGER')
    if 'public_id' not in columns:
        sync_connection.exec_driver_sql('ALTER TABLE merge_profiles ADD COLUMN public_id VARCHAR(36)')

    rows = sync_connection.exec_driver_sql('SELECT id, public_id FROM merge_profiles ORDER BY id').all()
    seen: set[str] = set()
    for profile_id, raw_public_id in rows:
        public_id = str(raw_public_id or '').strip()
        try:
            normalized = str(UUID(public_id))
        except ValueError:
            normalized = ''
        if not normalized or normalized in seen:
            normalized = str(uuid4())
            sync_connection.exec_driver_sql(
                'UPDATE merge_profiles SET public_id = ? WHERE id = ?',
                (normalized, profile_id),
            )
        seen.add(normalized)
    sync_connection.exec_driver_sql(
        'CREATE UNIQUE INDEX IF NOT EXISTS ix_merge_profiles_public_id ON merge_profiles(public_id)'
    )


def _ensure_template_columns(sync_connection: Connection) -> None:
    inspector = inspect(sync_connection)
    columns = {column['name'] for column in inspector.get_columns('templates')}
    if 'target' not in columns:
        sync_connection.exec_driver_sql("ALTER TABLE templates ADD COLUMN target VARCHAR(32) NOT NULL DEFAULT 'mihomo'")
    if 'schema_version' not in columns:
        sync_connection.exec_driver_sql(
            "ALTER TABLE templates ADD COLUMN schema_version VARCHAR(32) NOT NULL DEFAULT '1'"
        )
    if 'format' not in columns:
        sync_connection.exec_driver_sql("ALTER TABLE templates ADD COLUMN format VARCHAR(16) NOT NULL DEFAULT 'yaml'")

    sync_connection.exec_driver_sql("UPDATE templates SET target = 'mihomo' WHERE target IS NULL OR target = ''")
    sync_connection.exec_driver_sql(
        "UPDATE templates SET schema_version = '1' WHERE schema_version IS NULL OR schema_version = ''"
    )
    sync_connection.exec_driver_sql(
        "UPDATE templates SET format = 'yaml' WHERE format IS NULL OR format = '' OR lower(format) = 'clash'"
    )


def _ensure_subscription_columns(sync_connection: Connection) -> None:
    inspector = inspect(sync_connection)
    columns = {column['name'] for column in inspector.get_columns('subscriptions')}
    if 'cached_content' not in columns:
        sync_connection.exec_driver_sql('ALTER TABLE subscriptions ADD COLUMN cached_content TEXT')
    if 'last_updated_at' not in columns:
        sync_connection.exec_driver_sql('ALTER TABLE subscriptions ADD COLUMN last_updated_at DATETIME')
    if 'timeout_seconds' not in columns:
        sync_connection.exec_driver_sql(
            'ALTER TABLE subscriptions ADD COLUMN timeout_seconds FLOAT NOT NULL DEFAULT 5.0'
        )
    if 'excluded_node_names' not in columns:
        sync_connection.exec_driver_sql(
            "ALTER TABLE subscriptions ADD COLUMN excluded_node_names JSON NOT NULL DEFAULT '[]'"
        )
    sync_connection.exec_driver_sql('UPDATE subscriptions SET timeout_seconds = 5.0 WHERE timeout_seconds IS NULL')
    sync_connection.exec_driver_sql(
        "UPDATE subscriptions SET excluded_node_names = '[]' WHERE excluded_node_names IS NULL"
    )


def _ensure_rule_source_columns(sync_connection: Connection) -> None:
    inspector = inspect(sync_connection)
    columns = {column['name'] for column in inspector.get_columns('rule_sources')}
    if 'last_updated_at' not in columns:
        sync_connection.exec_driver_sql('ALTER TABLE rule_sources ADD COLUMN last_updated_at DATETIME')


def _drop_subscription_template_column(sync_connection: Connection) -> None:
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
                cached_content TEXT,
                last_updated_at DATETIME,
                proxy VARCHAR(2048),
                headers JSON NOT NULL,
                follow_redirects BOOLEAN NOT NULL,
                enabled BOOLEAN NOT NULL
            )
            """
        )
        has_cached_content = 'cached_content' in columns
        has_last_updated_at = 'last_updated_at' in columns
        if has_cached_content and has_last_updated_at:
            sync_connection.exec_driver_sql(
                """
                INSERT INTO subscriptions__new (
                    id, name, url, content, cached_content, last_updated_at, proxy, headers, follow_redirects, enabled
                )
                SELECT
                    id, name, url, content, cached_content, last_updated_at, proxy, headers, follow_redirects, enabled
                FROM subscriptions
                """
            )
        elif has_cached_content:
            sync_connection.exec_driver_sql(
                """
                INSERT INTO subscriptions__new (
                    id, name, url, content, cached_content, last_updated_at, proxy, headers, follow_redirects, enabled
                )
                SELECT
                    id, name, url, content, cached_content, NULL, proxy, headers, follow_redirects, enabled
                FROM subscriptions
                """
            )
        elif has_last_updated_at:
            sync_connection.exec_driver_sql(
                """
                INSERT INTO subscriptions__new (
                    id, name, url, content, cached_content, last_updated_at, proxy, headers, follow_redirects, enabled
                )
                SELECT
                    id, name, url, content, NULL, last_updated_at, proxy, headers, follow_redirects, enabled
                FROM subscriptions
                """
            )
        else:
            sync_connection.exec_driver_sql(
                """
                INSERT INTO subscriptions__new (
                    id, name, url, content, cached_content, last_updated_at, proxy, headers, follow_redirects, enabled
                )
                SELECT
                    id, name, url, content, NULL, NULL, proxy, headers, follow_redirects, enabled
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
        await connection.run_sync(_ensure_template_columns)
        await connection.run_sync(_drop_subscription_template_column)
        await connection.run_sync(_ensure_subscription_columns)
        await connection.run_sync(_ensure_rule_source_columns)


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
