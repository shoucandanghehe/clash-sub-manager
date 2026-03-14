"""Models for Clash-compatible configuration output."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ClashConfig(BaseModel):
    """A Clash configuration document.

    ``extra='allow'`` preserves template-owned keys we do not model explicitly,
    while aliases keep the Python API sane without changing emitted YAML keys.
    """

    model_config = ConfigDict(extra='allow', populate_by_name=True)

    port: int = 7890
    socks_port: int = Field(default=7891, alias='socks-port')
    mixed_port: int = Field(default=7892, alias='mixed-port')
    external_controller: str = Field(default='127.0.0.1:9090', alias='external-controller')
    proxies: list[dict[str, object]] = Field(default_factory=list)
    proxy_groups: list[dict[str, object]] = Field(default_factory=list, alias='proxy-groups')
    rules: list[str] = Field(default_factory=list)


__all__ = ['ClashConfig']
