"""Parser for Clash YAML configuration documents."""

from typing import Literal, cast

import yaml

from ..models import ClashConfig
from ..models.proxy import (
    AnyTLSNode,
    Hysteria2Node,
    ProxyNodeModel,
    ShadowsocksNode,
    ShadowsocksRNode,
    TrojanNode,
    VMessNode,
)
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
            case 'anytls':
                return cls._parse_anytls(proxy)
            case 'hysteria2':
                return cls._parse_hysteria2(proxy)
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
    def _parse_anytls(proxy: dict[str, object]) -> AnyTLSNode:
        require_keys(proxy, ('name', 'server', 'port', 'password'))
        return AnyTLSNode(
            name=str(proxy['name']),
            server=str(proxy['server']),
            port=ClashParser._int_value(proxy['port']),
            password=str(proxy['password']),
            udp=bool(proxy.get('udp', True)),
            sni=ClashParser._optional_string(proxy.get('sni')),
            skip_cert_verify=bool(proxy.get('skip-cert-verify', False)),
            client_fingerprint=ClashParser._optional_string(proxy.get('client-fingerprint')),
            alpn=ClashParser._string_list(proxy.get('alpn')),
            idle_session_check_interval=ClashParser._optional_int_value(proxy.get('idle-session-check-interval')),
            idle_session_timeout=ClashParser._optional_int_value(proxy.get('idle-session-timeout')),
            min_idle_session=ClashParser._optional_int_value(proxy.get('min-idle-session')),
            tfo=bool(proxy.get('tfo', False)),
        )

    @staticmethod
    def _parse_hysteria2(proxy: dict[str, object]) -> Hysteria2Node:
        require_keys(proxy, ('name', 'server', 'port'))
        ech_opts = ClashParser._mapping(proxy.get('ech-opts'))
        return Hysteria2Node(
            name=str(proxy['name']),
            server=str(proxy['server']),
            port=ClashParser._int_value(proxy['port']),
            password=str(proxy.get('password', '')),
            udp=bool(proxy.get('udp', True)),
            ports=ClashParser._optional_string_or_int(proxy.get('ports')),
            hop_interval=ClashParser._optional_string_or_int(proxy.get('hop-interval')),
            up=ClashParser._optional_string_or_int(proxy.get('up')),
            down=ClashParser._optional_string_or_int(proxy.get('down')),
            bbr_profile=ClashParser._optional_string(proxy.get('bbr-profile')),
            obfs=ClashParser._optional_string(proxy.get('obfs')),
            obfs_password=ClashParser._optional_string(proxy.get('obfs-password')),
            obfs_min_packet_size=ClashParser._optional_int_value(proxy.get('obfs-min-packet-size')),
            obfs_max_packet_size=ClashParser._optional_int_value(proxy.get('obfs-max-packet-size')),
            sni=ClashParser._optional_string(proxy.get('sni')),
            skip_cert_verify=bool(proxy.get('skip-cert-verify', False)),
            name_cert_verify=ClashParser._optional_string(proxy.get('name-cert-verify')),
            fingerprint=ClashParser._optional_string(proxy.get('fingerprint')),
            alpn=ClashParser._string_list(proxy.get('alpn')),
            ech_config=ClashParser._optional_string(ech_opts.get('config'))
            if bool(ech_opts.get('enable', False))
            else None,
            realm_opts=ClashParser._optional_mapping(proxy.get('realm-opts')),
            initial_stream_receive_window=ClashParser._optional_int_value(proxy.get('initial-stream-receive-window')),
            max_stream_receive_window=ClashParser._optional_int_value(proxy.get('max-stream-receive-window')),
            initial_connection_receive_window=ClashParser._optional_int_value(
                proxy.get('initial-connection-receive-window')
            ),
            max_connection_receive_window=ClashParser._optional_int_value(proxy.get('max-connection-receive-window')),
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
    def _optional_int_value(value: object) -> int | None:
        if value is None:
            return None
        return ClashParser._int_value(value)

    @staticmethod
    def _optional_string_or_int(value: object) -> str | int | None:
        if value is None:
            return None
        if isinstance(value, bool):
            msg = 'expected a string or integer value'
            raise TypeError(msg)
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        msg = 'expected a string or integer value'
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
    def _optional_mapping(value: object) -> dict[str, object] | None:
        if value is None:
            return None
        return ClashParser._mapping(value)

    @staticmethod
    def _string_mapping(value: object) -> dict[str, str] | None:
        if value is None:
            return None
        mapping = ClashParser._mapping(value)
        return {key: str(entry) for key, entry in mapping.items()}

    @staticmethod
    def _string_list(value: object) -> list[str] | None:
        if value is None:
            return None
        if not isinstance(value, list):
            msg = 'expected a list'
            raise TypeError(msg)
        result = [str(entry).strip() for entry in value if str(entry).strip()]
        return result or None

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
