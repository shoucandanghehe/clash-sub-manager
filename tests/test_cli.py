from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

from clash_sub_manager import cli

if TYPE_CHECKING:
    import pytest



def test_cli_help_lists_service_options() -> None:
    result = subprocess.run(
        [sys.executable, '-m', 'clash_sub_manager', '--help'],
        check=True,
        capture_output=True,
        text=True,
    )

    assert '--host' in result.stdout
    assert '--port' in result.stdout
    assert '--db-url' in result.stdout
    assert 'convert' not in result.stdout
    assert 'merge' not in result.stdout
    assert 'serve' not in result.stdout


def test_cli_main_starts_service_with_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_create_app(*, db_url: str) -> str:
        captured['db_url'] = db_url
        return 'app'

    def fake_run(app: object, *, host: str, port: int) -> None:
        captured['app'] = app
        captured['host'] = host
        captured['port'] = port

    monkeypatch.setattr(cli, 'create_app', fake_create_app)
    monkeypatch.setattr(cli.uvicorn, 'run', fake_run)

    cli.main([])

    assert captured == {
        'app': 'app',
        'db_url': 'sqlite+aiosqlite:///./clash_sub_manager.db',
        'host': '127.0.0.1',
        'port': 8000,
    }


def test_cli_main_accepts_host_port_and_db_url(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_create_app(*, db_url: str) -> str:
        captured['db_url'] = db_url
        return 'custom-app'

    def fake_run(app: object, *, host: str, port: int) -> None:
        captured['app'] = app
        captured['host'] = host
        captured['port'] = port

    monkeypatch.setattr(cli, 'create_app', fake_create_app)
    monkeypatch.setattr(cli.uvicorn, 'run', fake_run)

    cli.main(['--host', '127.0.0.2', '--port', '9000', '--db-url', 'sqlite+aiosqlite:///./custom.db'])

    assert captured == {
        'app': 'custom-app',
        'db_url': 'sqlite+aiosqlite:///./custom.db',
        'host': '127.0.0.2',
        'port': 9000,
    }
