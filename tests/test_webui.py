import pathlib
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from clash_sub_manager.api import create_app


@pytest.fixture
def client(tmp_path: pathlib.Path) -> Iterator[TestClient]:
    db_path = pathlib.Path(tmp_path) / 'webui.db'
    with TestClient(create_app(db_url=f'sqlite:///{db_path}')) as test_client:
        yield test_client


def test_webui_static_mount_serves_index(client: TestClient) -> None:
    response = client.get('/ui/')

    assert response.status_code == 200
    assert '<div id="app"></div>' in response.text
