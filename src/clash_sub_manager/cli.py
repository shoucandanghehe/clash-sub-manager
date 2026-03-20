"""Command-line entry point for starting the clash-sub-manager web service."""

from __future__ import annotations

import uvicorn
from cyclopts import App

from .api.server import create_app
from .db import default_db_url

app = App(
    help='Start the Clash Sub Manager HTTP API and WebUI service.',
    result_action='return_value',
)


@app.default
def serve(
    host: str = '127.0.0.1',
    port: int = 8000,
    db_url: str | None = None,
) -> None:
    """Start the Clash Sub Manager HTTP API and WebUI service.

    Parameters
    ----------
    host:
        Bind address for the HTTP service.
    port:
        Bind port for the HTTP service.
    db_url:
        Database URL passed into the FastAPI application factory. Defaults to the user app data directory when omitted.
    """

    uvicorn.run(create_app(db_url=db_url or default_db_url()), host=host, port=port)


def main(argv: list[str] | None = None) -> None:
    app(argv)
