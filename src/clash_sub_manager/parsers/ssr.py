"""Parser for ShadowsocksR share links."""

from __future__ import annotations

from urllib.parse import parse_qs

from typing_extensions import override

from ..models.proxy import ShadowsocksRNode
from .base import ShareLinkParser, decode_urlsafe_base64, first_query_value

_EXPECTED_SEGMENT_COUNT = 6


class ShadowsocksRParser(ShareLinkParser):
    scheme = 'ssr'

    @classmethod
    @override
    def parse(cls, url: str) -> ShadowsocksRNode:
        payload = decode_urlsafe_base64(url.removeprefix('ssr://'))
        main, _, raw_query = payload.partition('/?')
        segments = main.split(':')
        if len(segments) < _EXPECTED_SEGMENT_COUNT:
            msg = 'ssr link payload is incomplete'
            raise ValueError(msg)

        host = ':'.join(segments[:-5])
        port_text, protocol, cipher, obfs, password_payload = segments[-5:]
        query = parse_qs(raw_query, keep_blank_values=True)

        return ShadowsocksRNode(
            name=cls._decode_optional(query, 'remarks') or f'{host}:{port_text}',
            server=host,
            port=int(port_text),
            cipher=cipher,
            password=decode_urlsafe_base64(password_payload),
            protocol=protocol,
            protocol_param=cls._decode_optional(query, 'protoparam'),
            obfs=obfs,
            obfs_param=cls._decode_optional(query, 'obfsparam'),
        )

    @staticmethod
    def _decode_optional(query: dict[str, list[str]], key: str) -> str | None:
        value = first_query_value(query, key)
        if value is None:
            return None
        return decode_urlsafe_base64(value)
