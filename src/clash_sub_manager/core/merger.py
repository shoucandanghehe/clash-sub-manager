"""Strict subscription merging and deduplication."""

import asyncio
from collections.abc import Iterable
from dataclasses import dataclass

from ..models.clash import ClashConfig
from ..models.proxy import ProxyNodeModel
from ..models.subscription import SubscriptionConfig
from ..parsers import ProxyParser
from .converter import ClashConverter
from .fetcher import SubscriptionFetcher
from .template import TemplateProcessor


@dataclass(frozen=True, slots=True)
class NodeResolution:
    nodes: list[ProxyNodeModel]
    dropped_nodes: tuple[str, ...]


class SubscriptionMerger:
    """Merge multiple subscriptions with strict failure semantics."""

    def __init__(self, configs: list[SubscriptionConfig]):
        self.configs = configs

    async def resolve(self) -> NodeResolution:
        enabled_configs = [config for config in self.configs if config.enabled]
        if not enabled_configs:
            msg = 'at least one enabled subscription is required'
            raise ValueError(msg)
        contents = await asyncio.gather(*(SubscriptionFetcher(config).fetch() for config in enabled_configs))
        kept_nodes: list[ProxyNodeModel] = []
        dropped_nodes: list[str] = []
        for config, content in zip(enabled_configs, contents, strict=True):
            excluded_names = set(config.excluded_node_names)
            for node in ProxyParser.parse_subscription(content):
                if node.name in excluded_names:
                    dropped_nodes.append(node.name)
                else:
                    kept_nodes.append(node)
        return NodeResolution(self._deduplicate(kept_nodes), tuple(dropped_nodes))

    async def resolve_nodes(self) -> list[ProxyNodeModel]:
        return (await self.resolve()).nodes

    async def merge(self, template: TemplateProcessor | None = None) -> dict[str, object]:
        proxies = ClashConverter.convert_many((await self.resolve()).nodes)

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
        return self._freeze_identity_value(node.model_dump())

    def _freeze_identity_value(self, value: object) -> tuple[object, ...]:
        if isinstance(value, dict):
            return tuple(
                (str(key), self._freeze_identity_value(entry))
                for key, entry in sorted(value.items(), key=lambda item: str(item[0]))
            )
        if isinstance(value, list):
            return tuple(self._freeze_identity_value(entry) for entry in value)
        return ('value', value)


__all__ = ['NodeResolution', 'SubscriptionMerger']
