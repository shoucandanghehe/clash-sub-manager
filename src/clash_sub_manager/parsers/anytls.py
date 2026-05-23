"""Parser for AnyTLS share links."""

from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlsplit

from typing_extensions import override

from ..models.proxy import AnyTLSNode
from .base import ShareLinkParser, decode_fragment, parse_bool_flag


class AnyTLSParser(ShareLinkParser):
    scheme = 'anytls'

    @classmethod
    @override
    def parse(cls, url: str) -> AnyTLSNode:
        parts = urlsplit(url)
        host = parts.hostname
        port = parts.port or 443
        password = unquote(parts.username or '')
        if host is None or not password:
            msg = 'anytls link must include password and host'
            raise ValueError(msg)

        query = parse_qs(parts.query, keep_blank_values=True)
        return AnyTLSNode(
            name=decode_fragment(parts.fragment) or f'{host}:{port}',
            server=host,
            port=port,
            password=password,
            udp=cls._optional_bool(query, 'udp', default=True),
            sni=cls._first(query, 'sni'),
            skip_cert_verify=cls._optional_bool(query, 'insecure')
            or cls._optional_bool(query, 'allowInsecure')
            or cls._optional_bool(query, 'skip-cert-verify'),
            client_fingerprint=cls._first(query, 'client-fingerprint'),
            alpn=cls._alpn(query),
            idle_session_check_interval=cls._optional_int(query, 'idle-session-check-interval'),
            idle_session_timeout=cls._optional_int(query, 'idle-session-timeout'),
            min_idle_session=cls._optional_int(query, 'min-idle-session'),
            tfo=cls._optional_bool(query, 'tfo'),
        )

    @staticmethod
    def _first(query: dict[str, list[str]], key: str) -> str | None:
        values = query.get(key)
        if not values:
            return None
        value = values[0].strip()
        return value or None

    @classmethod
    def _optional_bool(cls, query: dict[str, list[str]], key: str, *, default: bool = False) -> bool:
        value = cls._first(query, key)
        if value is None:
            return default
        return parse_bool_flag(value)

    @classmethod
    def _optional_int(cls, query: dict[str, list[str]], key: str) -> int | None:
        value = cls._first(query, key)
        if value is None:
            return None
        return int(value)

    @staticmethod
    def _alpn(query: dict[str, list[str]]) -> list[str] | None:
        values = query.get('alpn')
        if not values:
            return None
        result = [entry.strip() for value in values for entry in value.split(',') if entry.strip()]
        return result or None
