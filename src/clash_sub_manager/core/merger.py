"""Strict subscription merging and deduplication."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from ..models.clash import ClashConfig
from ..models.proxy import ProxyNodeModel, ShadowsocksNode, ShadowsocksRNode, TrojanNode, VMessNode
from ..parsers import ProxyParser
from .converter import ClashConverter
from .fetcher import SubscriptionFetcher

if TYPE_CHECKING:
    from collections.abc import Iterable

    from ..models.subscription import SubscriptionConfig
    from .template import TemplateProcessor


class SubscriptionMerger:
    """Merge multiple subscriptions with strict failure semantics."""

    def __init__(self, configs: list[SubscriptionConfig]):
        self.configs = configs

    async def merge(self, template: TemplateProcessor | None = None) -> dict[str, object]:
        enabled_configs = [config for config in self.configs if config.enabled]
        if not enabled_configs:
            msg = 'at least one enabled subscription is required'
            raise ValueError(msg)

        contents = await asyncio.gather(*(SubscriptionFetcher(config).fetch() for config in enabled_configs))
        parsed_groups = [ProxyParser.parse_subscription(content) for content in contents]
        deduped_nodes = self._deduplicate(node for group in parsed_groups for node in group)
        proxies = ClashConverter.convert_many(deduped_nodes)

        if template is not None:
            return template.apply(proxies)

        proxy_group = {
            'name': 'Auto',
            'type': 'select',
            'proxies': [*(str(proxy['name']) for proxy in proxies), 'DIRECT'],
        }
        return ClashConfig.model_validate(
            {'proxies': proxies, 'proxy-groups': [proxy_group], 'rules': ['MATCH,Auto']},
        ).model_dump(by_alias=True, exclude_none=True)

    def _deduplicate(self, nodes: Iterable[ProxyNodeModel]) -> list[ProxyNodeModel]:
        unique: dict[tuple[object, ...], ProxyNodeModel] = {}
        for node in nodes:
            unique.setdefault(self._node_identity(node), node)
        return list(unique.values())

    def _node_identity(self, node: ProxyNodeModel) -> tuple[object, ...]:
        base = (node.type, node.server, node.port)
        if isinstance(node, ShadowsocksNode):
            return (
                *base,
                node.cipher,
                node.password,
                node.plugin,
                frozenset((node.plugin_opts or {}).items()),
            )
        if isinstance(node, ShadowsocksRNode):
            return (
                *base,
                node.cipher,
                node.password,
                node.protocol,
                node.protocol_param,
                node.obfs,
                node.obfs_param,
            )
        if isinstance(node, VMessNode):
            return (
                *base,
                node.uuid,
                node.alter_id,
                node.cipher,
                node.network,
                node.ws_path,
                frozenset(node.ws_headers.items()),
                node.grpc_service_name,
                node.tls,
            )
        if isinstance(node, TrojanNode):
            return (
                *base,
                node.password,
                node.network,
                node.ws_path,
                frozenset(node.ws_headers.items()),
                node.grpc_service_name,
                node.sni,
            )
        msg = f'unsupported proxy node: {type(node)!r}'
        raise TypeError(msg)


__all__ = ['SubscriptionMerger']
