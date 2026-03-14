"""Parser for VMess share links."""

from __future__ import annotations

import json
from typing import Literal, cast

from typing_extensions import override

from ..models.proxy import VMessNode
from .base import ShareLinkParser, decode_urlsafe_base64, parse_bool_flag, require_keys

SupportedNetwork = Literal['tcp', 'ws', 'grpc']


class VMessParser(ShareLinkParser):
    scheme = 'vmess'

    @classmethod
    @override
    def parse(cls, url: str) -> VMessNode:
        payload = decode_urlsafe_base64(url.removeprefix('vmess://'))
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            msg = 'vmess payload must be valid JSON'
            raise ValueError(msg) from exc
        if not isinstance(data, dict):
            msg = 'vmess payload must decode to an object'
            raise TypeError(msg)

        require_keys(data, ('add', 'port', 'id'))
        network = cls._parse_network(str(data.get('net', 'tcp') or 'tcp').lower())

        packet_type = str(data.get('type', '') or '').lower()
        if packet_type not in {'', 'none'}:
            msg = f'unsupported vmess transport type: {packet_type}'
            raise ValueError(msg)

        host_header = str(data.get('host', '') or '').strip()
        ws_headers = {'Host': host_header} if network == 'ws' and host_header else {}
        grpc_service_name = str(data.get('serviceName', '') or data.get('path', '') or '').strip() or None

        return VMessNode(
            name=str(data.get('ps', '') or f"{data['add']}:{data['port']}"),
            server=str(data['add']),
            port=int(str(data['port'])),
            uuid=str(data['id']),
            alter_id=int(str(data.get('aid', 0) or 0)),
            cipher=str(data.get('scy', 'auto') or 'auto'),
            tls=parse_bool_flag(str(data.get('tls', '') or '')),
            skip_cert_verify=parse_bool_flag(str(data.get('allowInsecure', '') or '')),
            servername=str(data.get('sni', '') or '').strip() or None,
            network=network,
            ws_path=str(data.get('path', '') or '').strip() or None,
            ws_headers=ws_headers,
            grpc_service_name=grpc_service_name,
        )

    @staticmethod
    def _parse_network(value: str) -> SupportedNetwork:
        if value not in {'tcp', 'ws', 'grpc'}:
            msg = f'unsupported vmess network: {value}'
            raise ValueError(msg)
        return cast('SupportedNetwork', value)
