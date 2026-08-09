"""Subscription and proxy parsers."""

from typing import ClassVar, cast

from ..models.proxy import (
    AnyTLSNode,
    Hysteria2Node,
    ProxyNodeModel,
    ShadowsocksNode,
    ShadowsocksRNode,
    TrojanNode,
    VMessNode,
)
from .anytls import AnyTLSParser
from .base import ShareLinkParser, decode_urlsafe_base64, split_subscription_entries
from .clash import ClashParser
from .hysteria2 import Hysteria2Parser
from .ss import ShadowsocksParser
from .ssr import ShadowsocksRParser
from .trojan import TrojanParser
from .vmess import VMessParser


def _has_uri_scheme(entry: str) -> bool:
    scheme, separator, _ = entry.partition('://')
    if not separator or not scheme:
        return False
    first = scheme[0].lower()
    return 'a' <= first <= 'z' and all(char.isascii() and (char.isalnum() or char in '+-.') for char in scheme)


class ProxyParser:
    """Facade over protocol-specific share-link parsers."""

    _PARSERS: ClassVar[dict[str, type[ShareLinkParser]]] = {
        'anytls://': AnyTLSParser,
        'hysteria2://': Hysteria2Parser,
        'hy2://': Hysteria2Parser,
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
        if direct_entries and all(_has_uri_scheme(entry) for entry in direct_entries):
            return [cls.parse_url(entry) for entry in direct_entries]

        try:
            return ClashParser.parse_proxies(stripped)
        except (TypeError, ValueError) as exc:
            clash_error = exc

        if direct_entries and any(_has_uri_scheme(entry) for entry in direct_entries):
            return [cls.parse_url(entry) for entry in direct_entries]

        try:
            decoded = decode_urlsafe_base64(stripped)
        except ValueError as exc:
            msg = f'unrecognized subscription format: {clash_error}'
            raise ValueError(msg) from exc

        decoded_entries = split_subscription_entries(decoded)
        if decoded_entries and all(_has_uri_scheme(entry) for entry in decoded_entries):
            return [cls.parse_url(entry) for entry in decoded_entries]

        try:
            return ClashParser.parse_proxies(decoded)
        except (TypeError, ValueError) as exc:
            if decoded_entries and any(_has_uri_scheme(entry) for entry in decoded_entries):
                return [cls.parse_url(entry) for entry in decoded_entries]
            msg = f'unrecognized decoded subscription format: {exc}'
            raise ValueError(msg) from exc

    @staticmethod
    def parse_anytls(url: str) -> AnyTLSNode:
        return AnyTLSParser.parse(url)

    @staticmethod
    def parse_hysteria2(url: str) -> Hysteria2Node:
        return Hysteria2Parser.parse(url)

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
    'AnyTLSParser',
    'ClashParser',
    'Hysteria2Parser',
    'ProxyParser',
    'ShadowsocksParser',
    'ShadowsocksRParser',
    'TrojanParser',
    'VMessParser',
]
