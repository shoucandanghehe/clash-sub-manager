"""Subscription and proxy parsers."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, cast

from .base import decode_urlsafe_base64, split_subscription_entries
from .clash import ClashParser
from .ss import ShadowsocksParser
from .ssr import ShadowsocksRParser
from .trojan import TrojanParser
from .vmess import VMessParser

if TYPE_CHECKING:
    from ..models.proxy import ProxyNodeModel, ShadowsocksNode, ShadowsocksRNode, TrojanNode, VMessNode
    from .base import ShareLinkParser


class ProxyParser:
    """Facade over protocol-specific share-link parsers."""

    _PARSERS: ClassVar[dict[str, type[ShareLinkParser]]] = {
        'ss://': ShadowsocksParser,
        'ssr://': ShadowsocksRParser,
        'vmess://': VMessParser,
        'trojan://': TrojanParser,
    }

    @classmethod
    def parse_url(cls, url: str) -> ProxyNodeModel:
        stripped = url.strip()
        for prefix, parser in cls._PARSERS.items():
            if stripped.startswith(prefix):
                return cast('ProxyNodeModel', parser.parse(stripped))
        msg = f'unsupported proxy scheme: {stripped[:16] or "<empty>"}'
        raise ValueError(msg)

    @classmethod
    def parse_subscription(cls, content: str) -> list[ProxyNodeModel]:
        stripped = content.strip()
        if not stripped:
            msg = 'subscription content must not be empty'
            raise ValueError(msg)

        direct_entries = split_subscription_entries(stripped)
        if direct_entries and all(entry.startswith(tuple(cls._PARSERS)) for entry in direct_entries):
            return [cls.parse_url(entry) for entry in direct_entries]

        try:
            return ClashParser.parse_proxies(stripped)
        except (TypeError, ValueError):
            pass

        decoded = decode_urlsafe_base64(stripped)
        decoded_entries = split_subscription_entries(decoded)
        if decoded_entries and all(entry.startswith(tuple(cls._PARSERS)) for entry in decoded_entries):
            return [cls.parse_url(entry) for entry in decoded_entries]
        return ClashParser.parse_proxies(decoded)

    @staticmethod
    def parse_ss(url: str) -> ShadowsocksNode:
        return ShadowsocksParser.parse(url)

    @staticmethod
    def parse_ssr(url: str) -> ShadowsocksRNode:
        return ShadowsocksRParser.parse(url)

    @staticmethod
    def parse_vmess(url: str) -> VMessNode:
        return VMessParser.parse(url)

    @staticmethod
    def parse_trojan(url: str) -> TrojanNode:
        return TrojanParser.parse(url)


__all__ = [
    'ClashParser',
    'ProxyParser',
    'ShadowsocksParser',
    'ShadowsocksRParser',
    'TrojanParser',
    'VMessParser',
]
