"""Parser for Clash YAML configuration documents."""

from __future__ import annotations

from typing import Literal, cast

import yaml

from ..models import ClashConfig
from ..models.proxy import ProxyNodeModel, ShadowsocksNode, ShadowsocksRNode, TrojanNode, VMessNode
from .base import require_keys

SupportedNetwork = Literal['tcp', 'ws', 'grpc']


class ClashParser:
    """Parse Clash YAML and convert supported proxy entries back into domain nodes."""

    @classmethod
    def parse_document(cls, content: str | dict[str, object]) -> ClashConfig:
        raw_document = yaml.safe_load(content) if isinstance(content, str) else content
        if not isinstance(raw_document, dict):
            msg = 'clash content must decode to a mapping'
            raise TypeError(msg)
        return ClashConfig.model_validate(raw_document)

    @classmethod
    def parse_proxies(cls, content: str | dict[str, object]) -> list[ProxyNodeModel]:
        document = cls.parse_document(content)
        return [cls._parse_proxy(proxy) for proxy in document.proxies]

    @classmethod
    def _parse_proxy(cls, proxy: dict[str, object]) -> ProxyNodeModel:
        raw_type = str(proxy.get('type', '')).strip().lower()
        match raw_type:
            case 'ss':
                return cls._parse_ss(proxy)
            case 'ssr':
                return cls._parse_ssr(proxy)
            case 'vmess':
                return cls._parse_vmess(proxy)
            case 'trojan':
                return cls._parse_trojan(proxy)
            case _:
                msg = f'unsupported clash proxy type: {raw_type or "<missing>"}'
                raise ValueError(msg)

    @staticmethod
    def _parse_ss(proxy: dict[str, object]) -> ShadowsocksNode:
        require_keys(proxy, ('name', 'server', 'port', 'cipher', 'password'))
        return ShadowsocksNode(
            name=str(proxy['name']),
            server=str(proxy['server']),
            port=ClashParser._int_value(proxy['port']),
            cipher=str(proxy['cipher']),
            password=str(proxy['password']),
            udp=bool(proxy.get('udp', True)),
            plugin=ClashParser._optional_string(proxy.get('plugin')),
            plugin_opts=ClashParser._string_mapping(proxy.get('plugin-opts')),
        )

    @staticmethod
    def _parse_ssr(proxy: dict[str, object]) -> ShadowsocksRNode:
        require_keys(proxy, ('name', 'server', 'port', 'cipher', 'password', 'protocol', 'obfs'))
        return ShadowsocksRNode(
            name=str(proxy['name']),
            server=str(proxy['server']),
            port=ClashParser._int_value(proxy['port']),
            cipher=str(proxy['cipher']),
            password=str(proxy['password']),
            protocol=str(proxy['protocol']),
            protocol_param=ClashParser._optional_string(proxy.get('protocol-param')),
            obfs=str(proxy['obfs']),
            obfs_param=ClashParser._optional_string(proxy.get('obfs-param')),
            udp=bool(proxy.get('udp', True)),
        )

    @staticmethod
    def _parse_vmess(proxy: dict[str, object]) -> VMessNode:
        require_keys(proxy, ('name', 'server', 'port', 'uuid'))
        ws_opts = ClashParser._mapping(proxy.get('ws-opts'))
        grpc_opts = ClashParser._mapping(proxy.get('grpc-opts'))
        return VMessNode(
            name=str(proxy['name']),
            server=str(proxy['server']),
            port=ClashParser._int_value(proxy['port']),
            uuid=str(proxy['uuid']),
            alter_id=ClashParser._int_value(proxy.get('alterId', 0)),
            cipher=str(proxy.get('cipher', 'auto') or 'auto'),
            udp=bool(proxy.get('udp', True)),
            tls=bool(proxy.get('tls', False)),
            skip_cert_verify=bool(proxy.get('skip-cert-verify', False)),
            servername=ClashParser._optional_string(proxy.get('servername')),
            network=ClashParser._network(proxy.get('network')),
            ws_path=ClashParser._optional_string(ws_opts.get('path')),
            ws_headers=ClashParser._string_mapping(ws_opts.get('headers')) or {},
            grpc_service_name=ClashParser._optional_string(grpc_opts.get('grpc-service-name')),
        )

    @staticmethod
    def _parse_trojan(proxy: dict[str, object]) -> TrojanNode:
        require_keys(proxy, ('name', 'server', 'port', 'password'))
        ws_opts = ClashParser._mapping(proxy.get('ws-opts'))
        grpc_opts = ClashParser._mapping(proxy.get('grpc-opts'))
        return TrojanNode(
            name=str(proxy['name']),
            server=str(proxy['server']),
            port=ClashParser._int_value(proxy['port']),
            password=str(proxy['password']),
            udp=bool(proxy.get('udp', True)),
            sni=ClashParser._optional_string(proxy.get('sni')),
            skip_cert_verify=bool(proxy.get('skip-cert-verify', False)),
            network=ClashParser._network(proxy.get('network')),
            ws_path=ClashParser._optional_string(ws_opts.get('path')),
            ws_headers=ClashParser._string_mapping(ws_opts.get('headers')) or {},
            grpc_service_name=ClashParser._optional_string(grpc_opts.get('grpc-service-name')),
        )

    @staticmethod
    def _int_value(value: object) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            return int(value)
        msg = 'expected an integer-compatible value'
        raise TypeError(msg)

    @staticmethod
    def _mapping(value: object) -> dict[str, object]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            msg = 'expected a mapping'
            raise TypeError(msg)
        return {str(key): entry for key, entry in value.items()}

    @staticmethod
    def _string_mapping(value: object) -> dict[str, str] | None:
        if value is None:
            return None
        mapping = ClashParser._mapping(value)
        return {key: str(entry) for key, entry in mapping.items()}

    @staticmethod
    def _optional_string(value: object) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None

    @staticmethod
    def _network(value: object) -> SupportedNetwork:
        normalized = str(value or 'tcp').lower()
        if normalized not in {'tcp', 'ws', 'grpc'}:
            msg = f'unsupported clash network: {normalized}'
            raise ValueError(msg)
        return cast('SupportedNetwork', normalized)
