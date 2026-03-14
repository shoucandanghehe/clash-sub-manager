import functools
import http.server
import pathlib
import socketserver
import threading
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from clash_sub_manager.api import create_app
from clash_sub_manager.core.rules import RuleManager
from clash_sub_manager.db import RuleSource, create_engine, init_db


@pytest.fixture
def rule_server(tmp_path: pathlib.Path) -> Iterator[str]:
    rules_path = pathlib.Path(tmp_path) / 'rules.txt'
    rules_path.write_text('# comment\nMATCH,DIRECT\nMATCH,DIRECT\nDOMAIN,example.com,Proxy\n', encoding='utf-8')
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp_path))
    server = socketserver.TCPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host = str(server.server_address[0])
        port = int(server.server_address[1])
        yield f'http://{host}:{port}/rules.txt'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.fixture
def client(tmp_path: pathlib.Path) -> Iterator[TestClient]:
    db_path = pathlib.Path(tmp_path) / 'api-rules.db'
    app = create_app(db_url=f'sqlite:///{db_path}')
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_rule_manager_updates_rule_source(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    engine = create_engine(f"sqlite:///{pathlib.Path(tmp_path) / 'rules.db'}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    manager = RuleManager()

    async def fake_fetch(
        url: str,
        *,
        headers: dict[str, str] | None = None,
        proxy: str | None = None,
        follow_redirects: bool = True,
    ) -> str:
        del headers, proxy, follow_redirects
        assert url == 'https://example.com/rules.txt'
        return '# comment\nMATCH,DIRECT\nMATCH,DIRECT\n'

    monkeypatch.setattr(manager, 'fetch_remote_content', fake_fetch)

    try:
        await init_db(engine)
        async with session_factory() as session:
            source = RuleSource(name='rules', url='https://example.com/rules.txt', auto_update=False, content=None)
            session.add(source)
            await session.commit()
            await session.refresh(source)

            content = await manager.update_rule_source(session, source)

            assert content == '# comment\nMATCH,DIRECT\nMATCH,DIRECT\n'
            assert source.content == content
            assert manager.parse_rules(content) == ['MATCH,DIRECT', 'MATCH,DIRECT']
    finally:
        await engine.dispose()


def test_cached_rule_provider_endpoint_returns_cached_content(client: TestClient) -> None:
    create_response = client.post(
        '/rule-sources',
        json={
            'name': 'applications',
            'url': 'https://example.com/applications.txt',
            'auto_update': False,
            'content': 'DOMAIN,example.com,DIRECT\n',
        },
    )
    assert create_response.status_code == 201
    source_id = create_response.json()['id']

    cached_response = client.get(f'/rule-providers/{source_id}')
    assert cached_response.status_code == 200
    assert cached_response.text == 'DOMAIN,example.com,DIRECT\n'


def test_rule_update_api_and_get_rules(client: TestClient, rule_server: str) -> None:
    create_response = client.post('/rule-sources', json={'name': 'rules', 'url': rule_server, 'auto_update': False})
    assert create_response.status_code == 201
    source_id = create_response.json()['id']

    update_response = client.post(f'/rule-sources/{source_id}/update')
    assert update_response.status_code == 200
    assert 'MATCH,DIRECT' in update_response.json()

    rules_response = client.get('/rules')
    assert rules_response.status_code == 200
    assert rules_response.json() == ['MATCH,DIRECT', 'DOMAIN,example.com,Proxy']

