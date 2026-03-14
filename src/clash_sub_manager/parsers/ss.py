"""Parser for Shadowsocks share links."""

from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlsplit

from typing_extensions import override

from ..models.proxy import ShadowsocksNode
from .base import ShareLinkParser, decode_fragment, decode_urlsafe_base64, parse_plugin_payload


class ShadowsocksParser(ShareLinkParser):
    scheme = 'ss'

    @classmethod
    @override
    def parse(cls, url: str) -> ShadowsocksNode:
        normalized = cls._normalize_legacy_url(url)
        parts = urlsplit(normalized)
        host = parts.hostname
        port = parts.port
        if host is None or port is None:
            msg = 'ss link must include host and port'
            raise ValueError(msg)

        userinfo = parts.netloc.rsplit('@', maxsplit=1)[0]
        method, password = cls._parse_userinfo(userinfo)

        plugin: str | None = None
        plugin_opts: dict[str, str] | None = None
        plugin_value = parse_qs(parts.query, keep_blank_values=True).get('plugin', [None])[0]
        if plugin_value:
            plugin, plugin_opts = parse_plugin_payload(unquote(plugin_value))

        return ShadowsocksNode(
            name=decode_fragment(parts.fragment) or f'{host}:{port}',
            server=host,
            port=port,
            cipher=method,
            password=password,
            plugin=plugin,
            plugin_opts=plugin_opts,
        )

    @classmethod
    def _normalize_legacy_url(cls, url: str) -> str:
        raw = url.removeprefix('ss://')
        main, has_fragment, fragment = raw.partition('#')
        base, has_query, query = main.partition('?')
        if '@' in base:
            return url
        decoded = decode_urlsafe_base64(base)
        suffix = f'?{query}' if has_query else ''
        fragment_suffix = f'#{fragment}' if has_fragment else ''
        return f'ss://{decoded}{suffix}{fragment_suffix}'

    @classmethod
    def _parse_userinfo(cls, userinfo: str) -> tuple[str, str]:
        decoded_userinfo = unquote(userinfo)
        if ':' in decoded_userinfo and not cls._looks_like_base64(decoded_userinfo):
            method, password = decoded_userinfo.split(':', maxsplit=1)
            return method, password
        decoded = decode_urlsafe_base64(decoded_userinfo)
        method, separator, password = decoded.partition(':')
        if not separator:
            msg = 'ss userinfo must be method:password'
            raise ValueError(msg)
        return method, password

    @staticmethod
    def _looks_like_base64(value: str) -> bool:
        return all(char.isalnum() or char in '-_=+/' for char in value)
