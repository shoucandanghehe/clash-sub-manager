from __future__ import annotations

import json
import pathlib

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import async_sessionmaker

import clash_sub_manager.db.session as db_session
from clash_sub_manager.db import (
    APP_DATA_DIR_NAME,
    DEFAULT_DB_FILENAME,
    CompositeTemplate,
    RuleSource,
    Subscription,
    Template,
    TemplatePatch,
    create_engine,
    default_db_path,
    default_db_url,
    init_db,
    normalize_async_db_url,
)


def test_normalize_async_db_url_for_sqlite() -> None:
    assert normalize_async_db_url('sqlite:///./demo.db') == 'sqlite+aiosqlite:///./demo.db'
    assert normalize_async_db_url('sqlite+aiosqlite:///./demo.db') == 'sqlite+aiosqlite:///./demo.db'


def test_default_db_uses_user_app_data_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    app_data_root = pathlib.Path(tmp_path) / 'app-data'

    def fake_user_data_path(*, appname: str, appauthor: bool, ensure_exists: bool) -> pathlib.Path:
        assert appname == APP_DATA_DIR_NAME
        assert appauthor is False
        assert ensure_exists is True
        app_data_root.mkdir(parents=True, exist_ok=True)
        return app_data_root

    monkeypatch.setattr(db_session, 'user_data_path', fake_user_data_path)

    assert default_db_path() == app_data_root / DEFAULT_DB_FILENAME
    assert default_db_url() == f'sqlite+aiosqlite:///{app_data_root / DEFAULT_DB_FILENAME}'


@pytest.mark.asyncio
async def test_init_db_creates_tables_and_supports_crud(tmp_path: pathlib.Path) -> None:
    db_path = pathlib.Path(tmp_path) / 'manager.db'
    engine = create_engine(f'sqlite:///{db_path}')
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        await init_db(engine)

        async with session_factory() as session:
            template = Template(name='default', content='proxies: []', is_default=True)
            session.add(template)
            await session.flush()

            subscription = Subscription(
                name='demo',
                url='https://example.com/sub',
                content=None,
                proxy=None,
                headers={'User-Agent': 'test'},
                follow_redirects=True,
                enabled=True,
            )
            rule_source = RuleSource(
                name='rules', url='https://example.com/rules', auto_update=True, content='MATCH,DIRECT'
            )
            template_patch = TemplatePatch(
                name='add-node',
                operations=[{'op': 'list_append', 'path': 'proxies', 'value': {'name': 'Node-A'}}],
            )
            composite_template = CompositeTemplate(
                name='derived',
                base_template_id=template.id,
                patch_sequence=[1],
                cached_content='proxies:\n  - name: Node-A\n',
            )
            session.add_all([subscription, rule_source, template_patch, composite_template])
            await session.commit()

        async with session_factory() as session:
            subscription_result = await session.execute(select(Subscription).where(Subscription.name == 'demo'))
            stored_subscription = subscription_result.scalar_one()
            rule_result = await session.execute(select(RuleSource).where(RuleSource.name == 'rules'))
            stored_rule_source = rule_result.scalar_one()
            patch_result = await session.execute(select(TemplatePatch).where(TemplatePatch.name == 'add-node'))
            stored_patch = patch_result.scalar_one()
            composite_result = await session.execute(
                select(CompositeTemplate).where(CompositeTemplate.name == 'derived')
            )
            stored_composite = composite_result.scalar_one()

            assert stored_subscription.headers == {'User-Agent': 'test'}
            assert stored_rule_source.content == 'MATCH,DIRECT'
            assert stored_patch.operations == [{'op': 'list_append', 'path': 'proxies', 'value': {'name': 'Node-A'}}]
            assert stored_composite.patch_sequence == [1]
            assert stored_composite.base_template_id == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_init_db_rebuilds_legacy_subscriptions_table(tmp_path: pathlib.Path) -> None:
    db_path = pathlib.Path(tmp_path) / 'legacy.db'
    engine = create_engine(f'sqlite:///{db_path}')

    try:
        async with engine.begin() as connection:
            await connection.exec_driver_sql(
                """
                CREATE TABLE subscriptions (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    url VARCHAR(2048),
                    content TEXT,
                    proxy VARCHAR(2048),
                    headers JSON NOT NULL,
                    follow_redirects BOOLEAN NOT NULL,
                    enabled BOOLEAN NOT NULL,
                    template_id INTEGER
                )
                """
            )
            await connection.exec_driver_sql(
                """
                INSERT INTO subscriptions (
                    id, name, url, content, proxy, headers, follow_redirects, enabled, template_id
                )
                VALUES (
                    1, 'legacy', 'https://example.com/sub', NULL, NULL, '{"User-Agent":"legacy"}', 1, 1, 99
                )
                """
            )

        await init_db(engine)

        async with engine.begin() as connection:

            def read_subscription_columns(sync_connection) -> tuple[list[str], tuple[str, str]]:
                inspector = inspect(sync_connection)
                columns = [column['name'] for column in inspector.get_columns('subscriptions')]
                row = sync_connection.exec_driver_sql('SELECT name, headers FROM subscriptions WHERE id = 1').one()
                return columns, (str(row[0]), str(row[1]))

            columns, stored_subscription = await connection.run_sync(read_subscription_columns)

        assert 'template_id' not in columns
        assert stored_subscription[0] == 'legacy'
        assert json.loads(stored_subscription[1]) == {'User-Agent': 'legacy'}
    finally:
        await engine.dispose()
