"""Parser for Trojan share links."""

from __future__ import annotations

from typing import Literal, cast
from urllib.parse import parse_qs, unquote, urlsplit

from typing_extensions import override

from ..models.proxy import TrojanNode
from .base import ShareLinkParser, decode_fragment, parse_bool_flag

SupportedNetwork = Literal['tcp', 'ws', 'grpc']


class TrojanParser(ShareLinkParser):
    scheme = 'trojan'

    @classmethod
    @override
    def parse(cls, url: str) -> TrojanNode:
        parts = urlsplit(url)
        host = parts.hostname
        port = parts.port or 443
        password = unquote(parts.username or '')
        if host is None or not password:
            msg = 'trojan link must include password and host'
            raise ValueError(msg)

        query = parse_qs(parts.query, keep_blank_values=True)
        raw_type = (query.get('type', ['tcp'])[0] or 'tcp').lower()
        network = cls._parse_network('tcp' if raw_type == 'original' else raw_type)

        ws_host = str(query.get('host', [''])[0] or '').strip()
        ws_headers = {'Host': ws_host} if network == 'ws' and ws_host else {}
        servername = str(query.get('sni', query.get('peer', ['']))[0] or '').strip() or None

        return TrojanNode(
            name=decode_fragment(parts.fragment) or f'{host}:{port}',
            server=host,
            port=port,
            password=password,
            skip_cert_verify=parse_bool_flag(query.get('allowInsecure', [''])[0]),
            sni=servername,
            network=network,
            ws_path=str(query.get('path', [''])[0] or '').strip() or None,
            ws_headers=ws_headers,
            grpc_service_name=str(query.get('serviceName', [''])[0] or '').strip() or None,
        )

    @staticmethod
    def _parse_network(value: str) -> SupportedNetwork:
        if value not in {'tcp', 'ws', 'grpc'}:
            msg = f'unsupported trojan network: {value}'
            raise ValueError(msg)
        return cast('SupportedNetwork', value)
