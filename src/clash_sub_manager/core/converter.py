"""Convert parsed proxy nodes into Clash-compatible dictionaries."""

from clash_sub_manager.models.proxy import (
    AnyTLSNode,
    Hysteria2Node,
    ProxyNodeModel,
    ShadowsocksNode,
    ShadowsocksRNode,
    TrojanNode,
    VMessNode,
)


class ClashConverter:
    """Translate protocol-specific node models into Clash proxy mappings."""

    @staticmethod
    def convert(node: ProxyNodeModel) -> dict[str, object]:
        match node:
            case ShadowsocksNode():
                return ClashConverter._convert_ss(node)
            case ShadowsocksRNode():
                return ClashConverter._convert_ssr(node)
            case VMessNode():
                return ClashConverter._convert_vmess(node)
            case TrojanNode():
                return ClashConverter._convert_trojan(node)
            case AnyTLSNode():
                return ClashConverter._convert_anytls(node)
            case Hysteria2Node():
                return ClashConverter._convert_hysteria2(node)
        msg = f'unsupported proxy node: {type(node)!r}'
        raise TypeError(msg)

    @staticmethod
    def convert_many(nodes: list[ProxyNodeModel]) -> list[dict[str, object]]:
        return [ClashConverter.convert(node) for node in nodes]

    @staticmethod
    def _convert_ss(node: ShadowsocksNode) -> dict[str, object]:
        proxy: dict[str, object] = {
            'name': node.name,
            'type': node.type,
            'server': node.server,
            'port': node.port,
            'cipher': node.cipher,
            'password': node.password,
            'udp': node.udp,
        }
        if node.plugin is not None:
            proxy['plugin'] = node.plugin
        if node.plugin_opts is not None:
            proxy['plugin-opts'] = node.plugin_opts
        return proxy

    @staticmethod
    def _convert_ssr(node: ShadowsocksRNode) -> dict[str, object]:
        proxy: dict[str, object] = {
            'name': node.name,
            'type': node.type,
            'server': node.server,
            'port': node.port,
            'cipher': node.cipher,
            'password': node.password,
            'protocol': node.protocol,
            'obfs': node.obfs,
            'udp': node.udp,
        }
        if node.protocol_param is not None:
            proxy['protocol-param'] = node.protocol_param
        if node.obfs_param is not None:
            proxy['obfs-param'] = node.obfs_param
        return proxy

    @staticmethod
    def _convert_vmess(node: VMessNode) -> dict[str, object]:
        proxy: dict[str, object] = {
            'name': node.name,
            'type': node.type,
            'server': node.server,
            'port': node.port,
            'uuid': node.uuid,
            'alterId': node.alter_id,
            'cipher': node.cipher,
            'udp': node.udp,
            'tls': node.tls,
        }
        if node.network != 'tcp':
            proxy['network'] = node.network
        if node.skip_cert_verify:
            proxy['skip-cert-verify'] = node.skip_cert_verify
        if node.servername is not None:
            proxy['servername'] = node.servername
        if node.network == 'ws':
            proxy['ws-opts'] = {
                'path': node.ws_path or '/',
                'headers': node.ws_headers,
            }
        if node.network == 'grpc' and node.grpc_service_name is not None:
            proxy['grpc-opts'] = {'grpc-service-name': node.grpc_service_name}
        return proxy

    @staticmethod
    def _convert_trojan(node: TrojanNode) -> dict[str, object]:
        proxy: dict[str, object] = {
            'name': node.name,
            'type': node.type,
            'server': node.server,
            'port': node.port,
            'password': node.password,
            'udp': node.udp,
        }
        if node.network != 'tcp':
            proxy['network'] = node.network
        if node.skip_cert_verify:
            proxy['skip-cert-verify'] = node.skip_cert_verify
        if node.sni is not None:
            proxy['sni'] = node.sni
        if node.network == 'ws':
            proxy['ws-opts'] = {
                'path': node.ws_path or '/',
                'headers': node.ws_headers,
            }
        if node.network == 'grpc' and node.grpc_service_name is not None:
            proxy['grpc-opts'] = {'grpc-service-name': node.grpc_service_name}
        return proxy

    @staticmethod
    def _convert_anytls(node: AnyTLSNode) -> dict[str, object]:
        proxy: dict[str, object] = {
            'name': node.name,
            'type': node.type,
            'server': node.server,
            'port': node.port,
            'password': node.password,
            'udp': node.udp,
        }
        if node.sni is not None:
            proxy['sni'] = node.sni
        if node.skip_cert_verify:
            proxy['skip-cert-verify'] = node.skip_cert_verify
        if node.client_fingerprint is not None:
            proxy['client-fingerprint'] = node.client_fingerprint
        if node.alpn is not None:
            proxy['alpn'] = node.alpn
        if node.idle_session_check_interval is not None:
            proxy['idle-session-check-interval'] = node.idle_session_check_interval
        if node.idle_session_timeout is not None:
            proxy['idle-session-timeout'] = node.idle_session_timeout
        if node.min_idle_session is not None:
            proxy['min-idle-session'] = node.min_idle_session
        if node.tfo:
            proxy['tfo'] = node.tfo
        return proxy

    @staticmethod
    def _convert_hysteria2(node: Hysteria2Node) -> dict[str, object]:
        proxy: dict[str, object] = {
            'name': node.name,
            'type': node.type,
            'server': node.server,
            'port': node.port,
            'password': node.password,
            'udp': node.udp,
        }
        ClashConverter._add_hysteria2_transport_options(proxy, node)
        ClashConverter._add_hysteria2_tls_options(proxy, node)
        ClashConverter._add_hysteria2_quic_options(proxy, node)
        return proxy

    @staticmethod
    def _add_hysteria2_transport_options(proxy: dict[str, object], node: Hysteria2Node) -> None:
        if node.ports is not None:
            proxy['ports'] = node.ports
        if node.hop_interval is not None:
            proxy['hop-interval'] = node.hop_interval
        if node.up is not None:
            proxy['up'] = node.up
        if node.down is not None:
            proxy['down'] = node.down
        if node.bbr_profile is not None:
            proxy['bbr-profile'] = node.bbr_profile
        if node.obfs is not None:
            proxy['obfs'] = node.obfs
        if node.obfs_password is not None:
            proxy['obfs-password'] = node.obfs_password
        if node.obfs_min_packet_size is not None:
            proxy['obfs-min-packet-size'] = node.obfs_min_packet_size
        if node.obfs_max_packet_size is not None:
            proxy['obfs-max-packet-size'] = node.obfs_max_packet_size

    @staticmethod
    def _add_hysteria2_tls_options(proxy: dict[str, object], node: Hysteria2Node) -> None:
        if node.sni is not None:
            proxy['sni'] = node.sni
        if node.skip_cert_verify:
            proxy['skip-cert-verify'] = node.skip_cert_verify
        if node.name_cert_verify is not None:
            proxy['name-cert-verify'] = node.name_cert_verify
        if node.fingerprint is not None:
            proxy['fingerprint'] = node.fingerprint
        if node.alpn is not None:
            proxy['alpn'] = node.alpn
        if node.ech_config is not None:
            proxy['ech-opts'] = {'enable': True, 'config': node.ech_config}
        if node.realm_opts is not None:
            proxy['realm-opts'] = node.realm_opts

    @staticmethod
    def _add_hysteria2_quic_options(proxy: dict[str, object], node: Hysteria2Node) -> None:
        if node.initial_stream_receive_window is not None:
            proxy['initial-stream-receive-window'] = node.initial_stream_receive_window
        if node.max_stream_receive_window is not None:
            proxy['max-stream-receive-window'] = node.max_stream_receive_window
        if node.initial_connection_receive_window is not None:
            proxy['initial-connection-receive-window'] = node.initial_connection_receive_window
        if node.max_connection_receive_window is not None:
            proxy['max-connection-receive-window'] = node.max_connection_receive_window


__all__ = ['ClashConverter']
