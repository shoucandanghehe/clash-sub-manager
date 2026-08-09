from __future__ import annotations

import base64
import contextlib
import http.server
import json
import threading
import time
from typing import TYPE_CHECKING, cast

import pytest
from typing_extensions import override

if TYPE_CHECKING:
    from collections.abc import Iterator

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
from clash_sub_manager.db import Template, TemplatePatch
from clash_sub_manager.models import SubscriptionConfig
from clash_sub_manager.parsers import ClashParser, ProxyParser


def _b64(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode('utf-8')).decode('utf-8').rstrip('=')


@pytest.fixture
def slow_subscription_url() -> Iterator[str]:
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            time.sleep(0.2)
            content = b'trojan://secret@example.com:443#Timeout'
            self.send_response(200)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            with contextlib.suppress(BrokenPipeError):
                self.wfile.write(content)

        @override
        def log_message(self, format: str, *args: object) -> None:
            del format, args

    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host = str(server.server_address[0])
        port = int(server.server_address[1])
        yield f'http://{host}:{port}/subscription'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


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
        f'{_b64("secret")}/?remarks={_b64("SSR Demo")}&obfsparam={_b64("cdn.example.com")}'
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


def test_parse_subscription_reports_unsupported_plain_link_scheme() -> None:
    content = (
        'trojan://secret@example.com:443#可用节点\n'
        'vless://12345678-1234-1234-1234-1234567890ab@example.com:443#不支持节点'
    )

    with pytest.raises(ValueError, match='unsupported proxy scheme: vless://'):
        ProxyParser.parse_subscription(content)


def test_parse_subscription_preserves_unescaped_spaces_in_fragment() -> None:
    nodes = ProxyParser.parse_subscription('trojan://secret@example.com:443#Hong Kong 01')

    assert [node.name for node in nodes] == ['Hong Kong 01']


def test_parse_subscription_reports_unsupported_clash_proxy_type() -> None:
    yaml_text = """
proxies:
  - name: 不支持节点
    type: vless
    server: example.com
    port: 443
    uuid: 12345678-1234-1234-1234-1234567890ab
"""

    with pytest.raises(ValueError, match='unsupported clash proxy type: vless'):
        ProxyParser.parse_subscription(yaml_text)


def test_parse_anytls_clash_proxy() -> None:
    yaml_text = """
proxies:
  - name: 日用香港
    type: anytls
    server: example.com
    port: "443"
    password: secret
    client-fingerprint: chrome
    udp: true
    idle-session-check-interval: 30
    idle-session-timeout: 30
    min-idle-session: 0
    sni: edge.example.com
    alpn:
      - h2
      - http/1.1
    skip-cert-verify: true
    tfo: true
"""

    expected_auth = 'secret'

    nodes = ProxyParser.parse_subscription(yaml_text)

    assert len(nodes) == 1
    node = nodes[0]
    assert node.type == 'anytls'
    assert node.name == '日用香港'
    assert node.password == expected_auth
    assert node.client_fingerprint == 'chrome'
    assert node.alpn == ['h2', 'http/1.1']
    assert node.idle_session_check_interval == 30
    assert node.idle_session_timeout == 30
    assert node.min_idle_session == 0
    assert node.sni == 'edge.example.com'
    assert node.skip_cert_verify is True
    assert node.tfo is True


def test_parse_anytls_share_link() -> None:
    expected_auth = 'letmein'

    node = ProxyParser.parse_anytls(
        'anytls://letmein@example.com:8443/?sni=real.example.com&insecure=1&alpn=h2,http/1.1#AnyTLS'
    )

    assert node.name == 'AnyTLS'
    assert node.server == 'example.com'
    assert node.port == 8443
    assert node.password == expected_auth
    assert node.sni == 'real.example.com'
    assert node.skip_cert_verify is True
    assert node.alpn == ['h2', 'http/1.1']


def test_converter_preserves_anytls_fields() -> None:
    nodes = ProxyParser.parse_subscription(
        """
proxies:
  - name: AnyTLS
    type: anytls
    server: example.com
    port: 443
    password: secret
    client-fingerprint: chrome
    udp: true
    idle-session-check-interval: 30
    idle-session-timeout: 30
    min-idle-session: 0
    sni: edge.example.com
    alpn:
      - h2
      - http/1.1
    skip-cert-verify: true
    tfo: true
"""
    )

    [proxy] = ClashConverter.convert_many(nodes)

    assert proxy == {
        'name': 'AnyTLS',
        'type': 'anytls',
        'server': 'example.com',
        'port': 443,
        'password': 'secret',
        'udp': True,
        'sni': 'edge.example.com',
        'skip-cert-verify': True,
        'client-fingerprint': 'chrome',
        'alpn': ['h2', 'http/1.1'],
        'idle-session-check-interval': 30,
        'idle-session-timeout': 30,
        'min-idle-session': 0,
        'tfo': True,
    }


def test_hysteria2_clash_proxy_round_trip_preserves_fields() -> None:
    nodes = ProxyParser.parse_subscription(
        """
proxies:
  - name: Hysteria2
    type: hysteria2
    server: example.com
    port: "443"
    ports: 443-8443
    hop-interval: 15-30
    password: secret
    up: 30
    down: 200 Mbps
    bbr-profile: aggressive
    obfs: gecko
    obfs-password: obfs-secret
    obfs-min-packet-size: 512
    obfs-max-packet-size: 1200
    sni: edge.example.com
    skip-cert-verify: true
    name-cert-verify: cert.example.com
    fingerprint: "SHA256:01:02:03"
    alpn:
      - h3
    realm-opts:
      enable: true
      server-url: https://realm.example.com
      token: public
    initial-stream-receive-window: 8388608
    max-stream-receive-window: 8388609
    initial-connection-receive-window: 20971520
    max-connection-receive-window: 20971521
"""
    )

    assert ClashConverter.convert_many(nodes) == [
        {
            'name': 'Hysteria2',
            'type': 'hysteria2',
            'server': 'example.com',
            'port': 443,
            'password': 'secret',
            'ports': '443-8443',
            'hop-interval': '15-30',
            'up': 30,
            'down': '200 Mbps',
            'bbr-profile': 'aggressive',
            'obfs': 'gecko',
            'obfs-password': 'obfs-secret',
            'obfs-min-packet-size': 512,
            'obfs-max-packet-size': 1200,
            'sni': 'edge.example.com',
            'skip-cert-verify': True,
            'name-cert-verify': 'cert.example.com',
            'fingerprint': 'SHA256:01:02:03',
            'alpn': ['h3'],
            'realm-opts': {
                'enable': True,
                'server-url': 'https://realm.example.com',
                'token': 'public',
            },
            'initial-stream-receive-window': 8388608,
            'max-stream-receive-window': 8388609,
            'initial-connection-receive-window': 20971520,
            'max-connection-receive-window': 20971521,
        }
    ]


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
async def test_subscription_fetcher_uses_each_subscription_timeout(slow_subscription_url: str) -> None:
    short_timeout = SubscriptionConfig.model_validate(
        {'name': 'short', 'url': slow_subscription_url, 'timeout_seconds': 0.05}
    )
    long_timeout = SubscriptionConfig.model_validate(
        {'name': 'long', 'url': slow_subscription_url, 'timeout_seconds': 1.0}
    )

    with pytest.raises(SubscriptionFetchError):
        await SubscriptionFetcher(short_timeout).fetch()

    assert await SubscriptionFetcher(long_timeout).fetch() == 'trojan://secret@example.com:443#Timeout'


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
async def test_subscription_merger_preserves_same_endpoint_with_distinct_names() -> None:
    clash_text = """
proxies:
  - name: "Alpha Label"
    type: ss
    server: same.example.com
    port: 8388
    cipher: aes-256-gcm
    password: secret
  - name: "Beta Label"
    type: ss
    server: same.example.com
    port: 8388
    cipher: aes-256-gcm
    password: secret
"""
    merged = await SubscriptionMerger([SubscriptionConfig(name='one', content=clash_text)]).merge()
    merged_proxies = cast('list[dict[str, object]]', merged['proxies'])
    merged_groups = cast('list[dict[str, object]]', merged['proxy-groups'])

    assert [proxy['name'] for proxy in merged_proxies] == ['Alpha Label', 'Beta Label']
    assert merged_groups[0]['proxies'] == ['Alpha Label', 'Beta Label', 'DIRECT']


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
    operations: list[dict[str, object]] = [
        {'op': 'set', 'path': 'proxy-groups.0.name', 'value': 'Patched'},
        {'op': 'list_insert', 'path': 'proxy-groups.0.proxies', 'index': 1, 'value': 'Node-B'},
        {'op': 'list_replace', 'path': 'proxy-groups.0.proxies', 'index': 2, 'old_value': 'Node-A', 'value': 'Node-C'},
        {'op': 'list_append', 'path': 'rules', 'value': 'DOMAIN,example.com,Patched'},
        {'op': 'merge', 'path': 'metadata', 'value': {'flags': {'stable': False}, 'tag': 'derived'}},
        {'op': 'delete', 'path': 'metadata.owner'},
    ]

    rendered = engine.apply(template, operations)
    rendered_proxy_groups = cast('list[dict[str, object]]', rendered['proxy-groups'])

    assert rendered == {
        'proxy-groups': [
            {'name': 'Patched', 'proxies': ['DIRECT', 'Node-B', 'Node-C']},
        ],
        'rules': ['MATCH,Auto', 'DOMAIN,example.com,Patched'],
        'metadata': {'flags': {'stable': False}, 'tag': 'derived'},
    }
    assert rendered_proxy_groups[0]['proxies'] == ['DIRECT', 'Node-B', 'Node-C']
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
        content=('proxy-groups:\n  - name: Auto\n    proxies:\n      - DIRECT\nrules:\n  - MATCH,Auto\n'),
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


def test_patch_engine_list_remove_uses_index_and_optional_old_value() -> None:
    engine = PatchEngine()
    template = {'proxy-groups': [{'name': 'Auto', 'proxies': ['DIRECT', 'Node-A', 'Node-B']}]}

    rendered = engine.apply(
        template,
        [
            {'op': 'list_remove', 'path': 'proxy-groups.0.proxies', 'index': 1, 'old_value': 'Node-A'},
        ],
    )
    rendered_proxy_groups = cast('list[dict[str, object]]', rendered['proxy-groups'])
    template_proxy_groups = cast('list[dict[str, object]]', template['proxy-groups'])

    assert rendered_proxy_groups[0]['proxies'] == ['DIRECT', 'Node-B']
    assert template_proxy_groups[0]['proxies'] == ['DIRECT', 'Node-A', 'Node-B']


def test_patch_engine_list_remove_rejects_old_value_mismatch() -> None:
    engine = PatchEngine()
    template = {'proxy-groups': [{'name': 'Auto', 'proxies': ['DIRECT', 'Node-A']}]}

    with pytest.raises(PatchValidationError, match='old_value mismatch'):
        engine.apply(
            template,
            [
                {'op': 'list_remove', 'path': 'proxy-groups.0.proxies', 'index': 1, 'old_value': 'Wrong-Node'},
            ],
        )
