from __future__ import annotations

import pathlib

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from clash_sub_manager.db import (
    CompositeTemplate,
    RuleSource,
    Subscription,
    Template,
    TemplatePatch,
    create_engine,
    init_db,
    normalize_async_db_url,
    )


def test_normalize_async_db_url_for_sqlite() -> None:
    assert normalize_async_db_url('sqlite:///./demo.db') == 'sqlite+aiosqlite:///./demo.db'
    assert normalize_async_db_url('sqlite+aiosqlite:///./demo.db') == 'sqlite+aiosqlite:///./demo.db'


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
                template_id=template.id,
            )
            rule_source = RuleSource(name='rules', url='https://example.com/rules', auto_update=True, content='MATCH,DIRECT')
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
            composite_result = await session.execute(select(CompositeTemplate).where(CompositeTemplate.name == 'derived'))
            stored_composite = composite_result.scalar_one()

            assert stored_subscription.headers == {'User-Agent': 'test'}
            assert stored_subscription.template_id == 1
            assert stored_rule_source.content == 'MATCH,DIRECT'
            assert stored_patch.operations == [{'op': 'list_append', 'path': 'proxies', 'value': {'name': 'Node-A'}}]
            assert stored_composite.patch_sequence == [1]
            assert stored_composite.base_template_id == 1
    finally:
        await engine.dispose()
