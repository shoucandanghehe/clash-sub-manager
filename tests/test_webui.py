import pathlib
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from clash_sub_manager.api import create_app
from clash_sub_manager.api import server as api_server


@pytest.fixture
def client(tmp_path: pathlib.Path) -> Iterator[TestClient]:
    db_path = pathlib.Path(tmp_path) / 'webui.db'
    webui_dir = pathlib.Path(tmp_path) / 'webui'
    webui_dir.mkdir()
    (webui_dir / 'index.html').write_text('<div id="app"></div>', encoding='utf-8')

    original_webui_static = api_server.WEBUI_STATIC
    api_server.WEBUI_STATIC = webui_dir
    try:
        with TestClient(create_app(db_url=f'sqlite:///{db_path}')) as test_client:
            yield test_client
    finally:
        api_server.WEBUI_STATIC = original_webui_static


def test_webui_static_mount_serves_index(client: TestClient) -> None:
    response = client.get('/ui/')

    assert response.status_code == 200
    assert '<div id="app"></div>' in response.text
