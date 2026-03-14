from __future__ import annotations

import base64
import json
from typing import cast

import pytest
import yaml

from clash_sub_manager.core import (
    ClashConverter,
    PatchEngine,
    PatchValidationError,
    SubscriptionFetcher,
    SubscriptionFetchError,
    SubscriptionMerger,
    TemplateComposer,
    TemplateProcessor,
)
from clash_sub_manager.db import CompositeTemplate, Template, TemplatePatch
from clash_sub_manager.models import SubscriptionConfig
from clash_sub_manager.parsers import ClashParser, ProxyParser


def _b64(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode('utf-8')).decode('utf-8').rstrip('=')


def test_parse_shadowsocks_sip002_link() -> None:
    encoded_userinfo = _b64('aes-256-gcm:secret')
    url = f'ss://{encoded_userinfo}@example.com:8388/?plugin=v2ray-plugin%3Bmode%3Dwebsocket#Demo'

    node = ProxyParser.parse_ss(url)

    assert node.name == 'Demo'
    assert node.plugin == 'v2ray-plugin'
    assert node.plugin_opts == {'mode': 'websocket'}


def test_parse_shadowsocksr_link() -> None:
    payload = (
        'example.com:8388:auth_sha1_v4:aes-256-cfb:tls1.2_ticket_auth:'
        f"{_b64('secret')}/?remarks={_b64('SSR Demo')}&obfsparam={_b64('cdn.example.com')}"
    )
    node = ProxyParser.parse_ssr(f'ssr://{_b64(payload)}')

    assert node.name == 'SSR Demo'
    assert node.obfs_param == 'cdn.example.com'


def test_parse_vmess_link() -> None:
    payload = {
        'ps': 'VMess Demo',
        'add': 'vmess.example.com',
        'port': '443',
        'id': '12345678-1234-1234-1234-1234567890ab',
        'aid': '0',
        'net': 'ws',
        'host': 'edge.example.com',
        'path': '/ws',
        'tls': 'tls',
        'scy': 'auto',
    }
    encoded = _b64(json.dumps(payload))

    node = ProxyParser.parse_vmess(f'vmess://{encoded}')

    assert node.servername is None
    assert node.ws_headers == {'Host': 'edge.example.com'}
    assert node.ws_path == '/ws'


def test_parse_trojan_link() -> None:
    url = (
        'trojan://secret@example.com:443'
        '?type=ws&host=edge.example.com&path=%2Fsocket&allowInsecure=1&sni=cdn.example.com#Trojan'
    )

    node = ProxyParser.parse_trojan(url)

    assert node.sni == 'cdn.example.com'
    assert node.skip_cert_verify is True
    assert node.ws_headers == {'Host': 'edge.example.com'}


def test_parse_subscription_from_base64_payload() -> None:
    encoded_userinfo = _b64('aes-256-gcm:secret')
    links = '\n'.join(
        [
            f'ss://{encoded_userinfo}@example.com:8388#One',
            'trojan://secret@example.com:443#Two',
        ]
    )

    nodes = ProxyParser.parse_subscription(_b64(links))

    assert [node.name for node in nodes] == ['One', 'Two']


def test_parse_clash_yaml_document() -> None:
    yaml_text = """
proxies:
  - name: Demo
    type: vmess
    server: vmess.example.com
    port: 443
    uuid: 12345678-1234-1234-1234-1234567890ab
    tls: true
    network: ws
    ws-opts:
      path: /ws
      headers:
        Host: edge.example.com
"""

    nodes = ClashParser.parse_proxies(yaml_text)

    assert nodes[0].type == 'vmess'
    assert nodes[0].ws_headers == {'Host': 'edge.example.com'}


def test_converter_builds_clash_ws_options() -> None:
    payload = {
        'ps': 'VMess Demo',
        'add': 'vmess.example.com',
        'port': '443',
        'id': '12345678-1234-1234-1234-1234567890ab',
        'aid': '0',
        'net': 'ws',
        'host': 'edge.example.com',
        'path': '/ws',
    }
    node = ProxyParser.parse_vmess(f'vmess://{_b64(json.dumps(payload))}')

    proxy = ClashConverter.convert(node)

    assert proxy['ws-opts'] == {'path': '/ws', 'headers': {'Host': 'edge.example.com'}}


def test_template_processor_keeps_groups_without_placeholders_unchanged() -> None:
    template = TemplateProcessor(
        {
            'proxy-groups': [
                {'name': 'Auto', 'type': 'select', 'proxies': ['DIRECT']},
            ],
        }
    )

    rendered = template.apply([{'name': 'Demo', 'type': 'ss'}])
    rendered_groups = cast('list[dict[str, object]]', rendered['proxy-groups'])

    assert rendered_groups[0]['proxies'] == ['DIRECT']
    assert rendered['rules'] == ['MATCH,Auto']


def test_template_processor_expands_proxy_placeholders() -> None:
    template = TemplateProcessor(
        {
            'proxy-groups': [
                {'name': 'Auto', 'type': 'select', 'proxies': ['DIRECT', '__all_proxies__']},
                {'name': 'HK Only', 'type': 'select', 'proxies': ['DIRECT', '__hk_proxies__']},
                {'name': 'Tagged', 'type': 'select', 'proxies': ['DIRECT', '__manual_proxies__', '__hk_proxies__']},
            ],
        }
    )

    rendered = template.apply(
        [
            {'name': 'HK-01', 'type': 'ss'},
            {'name': '日本-01', 'type': 'ss'},
            {'name': 'manual-special', 'type': 'ss'},
            {'name': 'US-01', 'type': 'ss'},
        ]
    )
    rendered_groups = cast('list[dict[str, object]]', rendered['proxy-groups'])

    assert rendered_groups[0]['proxies'] == ['DIRECT', 'HK-01', '日本-01', 'manual-special', 'US-01']
    assert rendered_groups[1]['proxies'] == ['DIRECT', 'HK-01']
    assert rendered_groups[2]['proxies'] == ['DIRECT', 'manual-special', 'HK-01']
    assert rendered['rules'] == ['MATCH,Auto']


def test_template_processor_rewrites_rule_provider_urls() -> None:
    template = TemplateProcessor(
        {
            'rule-providers': {
                'applications': {
                    'type': 'http',
                    'behavior': 'classical',
                    'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/applications.txt',
                    'path': './ruleset/applications.yaml',
                    'interval': 86400,
                },
            },
        },
        rule_provider_urls={
            'applications': 'http://testserver/rule-providers/1',
        },
    )

    rendered = template.apply([{'name': 'Demo', 'type': 'ss'}])
    providers = cast('dict[str, dict[str, object]]', rendered['rule-providers'])

    assert providers['applications']['url'] == 'http://testserver/rule-providers/1'


@pytest.mark.asyncio
async def test_subscription_merger_deduplicates_nodes() -> None:
    encoded_userinfo = _b64('aes-256-gcm:secret')
    link = f'ss://{encoded_userinfo}@example.com:8388#Same'
    configs = [
        SubscriptionConfig(name='one', content=_b64(link)),
        SubscriptionConfig(name='two', content=_b64(link)),
    ]

    merged = await SubscriptionMerger(configs).merge()
    merged_proxies = cast('list[dict[str, object]]', merged['proxies'])
    merged_groups = cast('list[dict[str, object]]', merged['proxy-groups'])

    assert len(merged_proxies) == 1
    assert merged_groups[0]['proxies'] == ['Same', 'DIRECT']


@pytest.mark.asyncio
async def test_subscription_merger_fails_strictly_on_fetch_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_fetch(self: SubscriptionFetcher) -> str:
        if self.config.name == 'broken':
            message = 'boom'
            raise SubscriptionFetchError(message)
        return _b64('trojan://secret@example.com:443#Ok')

    monkeypatch.setattr(SubscriptionFetcher, 'fetch', fake_fetch)
    configs = [
        SubscriptionConfig(name='ok', content='trojan://ignored'),
        SubscriptionConfig(name='broken', content='trojan://ignored'),
    ]

    with pytest.raises(SubscriptionFetchError):
        await SubscriptionMerger(configs).merge()


def test_patch_engine_applies_ordered_operations_without_mutating_input() -> None:
    engine = PatchEngine()
    template = {
        'proxy-groups': [
            {'name': 'Auto', 'proxies': ['DIRECT', 'Node-A']},
        ],
        'rules': ['MATCH,Auto'],
        'metadata': {'owner': 'base', 'flags': {'stable': True}},
    }
    operations = [
        {'op': 'set', 'path': 'proxy-groups.0.name', 'value': 'Patched'},
        {'op': 'list_insert', 'path': 'proxy-groups.0.proxies', 'index': 1, 'value': 'Node-B'},
        {'op': 'list_replace', 'path': 'proxy-groups.0.proxies', 'index': 2, 'old_value': 'Node-A', 'value': 'Node-C'},
        {'op': 'list_append', 'path': 'rules', 'value': 'DOMAIN,example.com,Patched'},
        {'op': 'merge', 'path': 'metadata', 'value': {'flags': {'stable': False}, 'tag': 'derived'}},
        {'op': 'delete', 'path': 'metadata.owner'},
    ]

    rendered = engine.apply(template, operations)

    assert rendered == {
        'proxy-groups': [
            {'name': 'Patched', 'proxies': ['DIRECT', 'Node-B', 'Node-C']},
        ],
        'rules': ['MATCH,Auto', 'DOMAIN,example.com,Patched'],
        'metadata': {'flags': {'stable': False}, 'tag': 'derived'},
    }
    assert template == {
        'proxy-groups': [
            {'name': 'Auto', 'proxies': ['DIRECT', 'Node-A']},
        ],
        'rules': ['MATCH,Auto'],
        'metadata': {'owner': 'base', 'flags': {'stable': True}},
    }


def test_patch_engine_rejects_invalid_paths_atomically() -> None:
    engine = PatchEngine()
    template = {'proxy-groups': [{'name': 'Auto', 'proxies': ['DIRECT']}]}
    operations = [
        {'op': 'list_append', 'path': 'proxy-groups.0.proxies', 'value': 'Node-A'},
        {'op': 'set', 'path': 'proxy-groups.1.name', 'value': 'Broken'},
    ]

    with pytest.raises(PatchValidationError, match='out of range'):
        engine.apply(template, operations)

    assert template == {'proxy-groups': [{'name': 'Auto', 'proxies': ['DIRECT']}]}


def test_template_composer_applies_patch_sequence_in_order() -> None:
    composer = TemplateComposer()
    base_template = Template(
        name='base',
        content=(
            'proxy-groups:\n'
            '  - name: Auto\n'
            '    proxies:\n'
            '      - DIRECT\n'
            'rules:\n'
            '  - MATCH,Auto\n'
        ),
        is_default=False,
    )
    patches = [
        TemplatePatch(
            name='rename-group',
            operations=[{'op': 'set', 'path': 'proxy-groups.0.name', 'value': 'Select'}],
        ),
        TemplatePatch(
            name='append-rule',
            operations=[{'op': 'list_append', 'path': 'rules', 'value': 'DOMAIN,example.com,Select'}],
        ),
    ]

    rendered = composer.compose(base_template, patches)

    assert rendered['proxy-groups'] == [{'name': 'Select', 'proxies': ['DIRECT']}]
    assert rendered['rules'] == ['MATCH,Auto', 'DOMAIN,example.com,Select']


def test_template_composer_refreshes_composite_cache() -> None:
    composer = TemplateComposer()
    base_template = Template(name='base', content='proxies: []\n', is_default=False)
    composite = CompositeTemplate(
        name='derived',
        base_template=base_template,
        patch_sequence=[1],
        cached_content='',
    )
    patches = [
        TemplatePatch(name='append-proxy', operations=[{'op': 'list_append', 'path': 'proxies', 'value': {'name': 'Node-A'}}]),
    ]

    rendered = composer.refresh_composite(composite, patches)

    assert rendered == {'proxies': [{'name': 'Node-A'}]}
    assert yaml.safe_load(composite.cached_content) == rendered
