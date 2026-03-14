"""Apply Clash proxy output onto YAML templates."""

from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from collections.abc import Mapping

_PLACEHOLDER_PATTERN = re.compile(r'^__([a-z0-9]+)_proxies__$')
_SHORT_TOKEN_MAX_LENGTH = 2
_PLACEHOLDER_ALIASES: dict[str, tuple[str, ...]] = {
    'hk': ('hkg', 'hong kong', 'hongkong', '香港', 'hkbn', 'hgc', '🇭🇰'),
    'tw': ('twn', 'taiwan', '台灣', '台湾', '🇹🇼'),
    'jp': ('jpn', 'japan', '日本', '东京', '大阪', '泉日', '🇯🇵'),
    'sg': ('sgp', 'singapore', '新加坡', '狮城', '🇸🇬'),
    'us': ('usa', 'united states', 'america', '美国', '洛杉矶', '西雅图', '圣何塞', '硅谷', '纽约', '达拉斯', '🇺🇸'),
    'kr': ('kor', 'korea', 'korean', '韩国', '首尔', '春川', '🇰🇷'),
    'de': ('deu', 'germany', '德国', '法兰克福', '柏林', '🇩🇪'),
    'uk': ('gb', 'gbr', 'united kingdom', 'britain', '英国', '伦敦', '🇬🇧'),
}


class TemplateProcessor:
    """Load a template document and inject proxies without mutating the source.

    Proxy groups support placeholder entries shaped like ``__all_proxies__`` or
    ``__hk_proxies__``. Placeholders expand in place and preserve surrounding
    static entries such as ``DIRECT`` or nested selector group names.

    Rule providers may also be rewritten to project-served cached URLs when the
    caller supplies a mapping keyed by provider name and/or original provider URL.
    """

    def __init__(
        self,
        template: dict[str, object] | Path,
        *,
        rule_provider_urls: Mapping[str, str] | None = None,
    ):
        if isinstance(template, Path):
            raw_template = yaml.safe_load(template.read_text(encoding='utf-8'))
        else:
            raw_template = deepcopy(template)
        if not isinstance(raw_template, dict):
            msg = 'template content must decode to a mapping'
            raise TypeError(msg)
        self.template = raw_template
        self.rule_provider_urls = dict(rule_provider_urls or {})

    def apply(
        self,
        proxies: list[dict[str, object]],
        proxy_groups: list[dict[str, object]] | None = None,
        rules: list[str] | None = None,
    ) -> dict[str, object]:
        result = deepcopy(self.template)
        result['proxies'] = proxies

        if self.rule_provider_urls:
            rule_providers = result.get('rule-providers')
            if isinstance(rule_providers, dict):
                result['rule-providers'] = self._rewrite_rule_providers(rule_providers)

        proxy_names = [str(proxy['name']) for proxy in proxies]
        if proxy_groups is not None:
            if not proxy_groups:
                msg = 'proxy_groups must not be empty when provided'
                raise ValueError(msg)
            result['proxy-groups'] = proxy_groups
            default_group_name = str(proxy_groups[0]['name'])
        elif 'proxy-groups' in result:
            merged_groups = self._merge_groups(result.get('proxy-groups', []), proxy_names)
            if merged_groups:
                result['proxy-groups'] = merged_groups
                default_group_name = str(merged_groups[0]['name'])
            else:
                default_group = self._default_group(proxy_names)
                result['proxy-groups'] = [default_group]
                default_group_name = str(default_group['name'])
        else:
            default_group = self._default_group(proxy_names)
            result['proxy-groups'] = [default_group]
            default_group_name = str(default_group['name'])

        if rules is not None:
            result['rules'] = rules
        elif 'rules' not in result:
            result['rules'] = [f'MATCH,{default_group_name}']
        return result

    def _rewrite_rule_providers(self, providers: dict[object, object]) -> dict[object, object]:
        rewritten: dict[object, object] = {}
        for provider_name, provider in providers.items():
            if not isinstance(provider, dict):
                rewritten[provider_name] = provider
                continue

            updated = deepcopy(provider)
            replacement = self._resolve_rule_provider_url(provider_name, updated)
            if replacement is not None:
                updated['url'] = replacement
            rewritten[provider_name] = updated
        return rewritten

    def _resolve_rule_provider_url(self, provider_name: object, provider: dict[object, object]) -> str | None:
        name_key = str(provider_name)
        if name_key in self.rule_provider_urls:
            return self.rule_provider_urls[name_key]

        url = provider.get('url')
        if isinstance(url, str) and url in self.rule_provider_urls:
            return self.rule_provider_urls[url]
        return None

    def _merge_groups(self, groups: object, proxy_names: list[str]) -> list[dict[str, object]]:
        if not isinstance(groups, list):
            msg = 'template proxy-groups must be a list'
            raise TypeError(msg)
        merged: list[dict[str, object]] = []
        for group in groups:
            if not isinstance(group, dict):
                msg = 'template proxy-groups entries must be mappings'
                raise TypeError(msg)
            updated = deepcopy(group)
            proxies = updated.get('proxies')
            if isinstance(proxies, list):
                updated['proxies'] = self._expand_group_proxies(proxies, proxy_names)
            merged.append(updated)
        return merged

    def _expand_group_proxies(self, proxies: list[object], proxy_names: list[str]) -> list[object]:
        expanded: list[object] = []
        seen_names: set[str] = set()
        for entry in proxies:
            placeholder_matches = self._resolve_placeholder(entry, proxy_names)
            if placeholder_matches is not None:
                for name in placeholder_matches:
                    if name not in seen_names:
                        expanded.append(name)
                        seen_names.add(name)
                continue

            entry_name = str(entry)
            if entry_name not in seen_names:
                expanded.append(entry)
                seen_names.add(entry_name)

        return expanded

    def _resolve_placeholder(self, entry: object, proxy_names: list[str]) -> list[str] | None:
        if not isinstance(entry, str):
            return None

        match = _PLACEHOLDER_PATTERN.fullmatch(entry.strip())
        if match is None:
            return None

        selector = match.group(1)
        if selector == 'all':
            return proxy_names

        return [name for name in proxy_names if self._name_matches_placeholder(name, selector)]

    def _name_matches_placeholder(self, proxy_name: str, selector: str) -> bool:
        aliases = (selector, *_PLACEHOLDER_ALIASES.get(selector, ()))
        return any(self._alias_matches_name(proxy_name, alias) for alias in aliases)

    def _alias_matches_name(self, proxy_name: str, alias: str) -> bool:
        raw_name = proxy_name.casefold()
        raw_alias = alias.casefold().strip()
        if not raw_alias:
            return False

        if any(not character.isascii() or not character.isalnum() for character in raw_alias) and raw_alias in raw_name:
            return True

        normalized_name = self._normalize_for_match(raw_name)
        normalized_alias = self._normalize_for_match(raw_alias)
        if not normalized_alias:
            return False

        name_tokens = set(normalized_name.split())
        alias_tokens = normalized_alias.split()
        if len(alias_tokens) == 1:
            alias_token = alias_tokens[0]
            if len(alias_token) <= _SHORT_TOKEN_MAX_LENGTH:
                return alias_token in name_tokens
            return alias_token in name_tokens or alias_token in normalized_name.replace(' ', '')

        collapsed_name = normalized_name.replace(' ', '')
        collapsed_alias = normalized_alias.replace(' ', '')
        return normalized_alias in normalized_name or collapsed_alias in collapsed_name

    @staticmethod
    def _normalize_for_match(value: str) -> str:
        return re.sub(r'[^0-9a-z\u4e00-\u9fff]+', ' ', value.casefold()).strip()

    @staticmethod
    def _default_group(proxy_names: list[str]) -> dict[str, object]:
        return {
            'name': 'Auto',
            'type': 'select',
            'proxies': [*proxy_names, 'DIRECT'],
        }


__all__ = ['TemplateProcessor']
