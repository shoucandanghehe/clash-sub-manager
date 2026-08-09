"""Parser for Hysteria 2 share links."""

from urllib.parse import parse_qs, unquote, urlsplit

from typing_extensions import override

from ..models.proxy import Hysteria2Node
from .base import ShareLinkParser, decode_fragment, first_query_value

_MAX_PORT = 65535


class Hysteria2Parser(ShareLinkParser):
    scheme = 'hysteria2'
    aliases = frozenset({'hysteria2', 'hy2'})

    @classmethod
    @override
    def parse(cls, url: str) -> Hysteria2Node:
        parts = urlsplit(url)
        if parts.scheme not in cls.aliases:
            msg = f'unsupported hysteria2 scheme: {parts.scheme or "<missing>"}'
            raise ValueError(msg)

        raw_auth, separator, _ = parts.netloc.rpartition('@')
        password = unquote(raw_auth) if separator else ''
        host = parts.hostname
        if host is None:
            msg = 'hysteria2 link must include a host'
            raise ValueError(msg)

        port_spec = cls._port_spec(parts.netloc)
        port, ports = cls._ports(port_spec)
        query = parse_qs(parts.query, keep_blank_values=True)
        obfs = first_query_value(query, 'obfs')
        if obfs not in {None, 'salamander', 'gecko'}:
            msg = f'unsupported hysteria2 obfs type: {obfs}'
            raise ValueError(msg)
        obfs_password = first_query_value(query, 'obfs-password')
        if (obfs is None) != (obfs_password is None):
            msg = 'hysteria2 obfs and obfs-password must be configured together'
            raise ValueError(msg)

        return Hysteria2Node(
            name=decode_fragment(parts.fragment) or f'{host}:{port_spec or port}',
            server=host,
            port=port,
            ports=ports,
            password=password,
            obfs=obfs,
            obfs_password=obfs_password,
            sni=first_query_value(query, 'sni'),
            skip_cert_verify=cls._insecure(query),
            fingerprint=first_query_value(query, 'pinSHA256'),
            ech_config=first_query_value(query, 'ech'),
        )

    @staticmethod
    def _port_spec(netloc: str) -> str | None:
        authority = netloc.rsplit('@', maxsplit=1)[-1]
        if authority.startswith('['):
            closing_bracket = authority.find(']')
            if closing_bracket < 0:
                msg = 'hysteria2 IPv6 host must have a closing bracket'
                raise ValueError(msg)
            remainder = authority[closing_bracket + 1 :]
            if not remainder:
                return None
            if not remainder.startswith(':'):
                msg = 'invalid hysteria2 server authority'
                raise ValueError(msg)
            return unquote(remainder[1:])

        if authority.count(':') > 1:
            msg = 'hysteria2 IPv6 host must be enclosed in brackets'
            raise ValueError(msg)
        _, separator, raw_port_spec = authority.rpartition(':')
        return unquote(raw_port_spec) if separator else None

    @classmethod
    def _ports(cls, port_spec: str | None) -> tuple[int, str | None]:
        if port_spec is None:
            return 443, None
        tokens = [token.strip() for token in port_spec.split(',')]
        if not tokens or any(not token for token in tokens):
            msg = 'invalid hysteria2 port specification'
            raise ValueError(msg)

        first_port = 0
        has_range = False
        for index, token in enumerate(tokens):
            start, separator, end = token.partition('-')
            if not start.isdecimal() or (separator and (not end.isdecimal() or '-' in end)):
                msg = f'invalid hysteria2 port entry: {token}'
                raise ValueError(msg)
            start_port = cls._port(start)
            if separator:
                has_range = True
                end_port = cls._port(end)
                if start_port > end_port:
                    msg = f'invalid hysteria2 port range: {token}'
                    raise ValueError(msg)
            if index == 0:
                first_port = start_port

        normalized = ','.join(tokens)
        return first_port, normalized if len(tokens) > 1 or has_range else None

    @staticmethod
    def _port(value: str) -> int:
        port = int(value)
        if not 1 <= port <= _MAX_PORT:
            msg = f'hysteria2 port out of range: {port}'
            raise ValueError(msg)
        return port

    @staticmethod
    def _insecure(query: dict[str, list[str]]) -> bool:
        value = first_query_value(query, 'insecure')
        if value is None:
            return False
        if value not in {'0', '1'}:
            msg = 'hysteria2 insecure must be 0 or 1'
            raise ValueError(msg)
        return value == '1'


__all__ = ['Hysteria2Parser']
