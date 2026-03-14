"""Convert parsed proxy nodes into Clash-compatible dictionaries."""

from __future__ import annotations

from clash_sub_manager.models.proxy import (
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


__all__ = ['ClashConverter']
