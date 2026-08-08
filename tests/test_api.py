import hashlib
import json
import pathlib
from collections.abc import Iterator

import pytest
import yaml
from fastapi.testclient import TestClient

from clash_sub_manager.api import create_app
from clash_sub_manager.core import SubscriptionFetcher, SubscriptionFetchError


@pytest.fixture
def client(tmp_path: pathlib.Path) -> Iterator[TestClient]:
    db_path = pathlib.Path(tmp_path) / 'api.db'
    app = create_app(db_url=f'sqlite:///{db_path}')
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sing_box_client(tmp_path: pathlib.Path) -> Iterator[TestClient]:
    db_path = pathlib.Path(tmp_path) / 'sing-box-api.db'
    artifact_dir = pathlib.Path(tmp_path) / 'sing-box-artifacts'
    binary_path = pathlib.Path(tmp_path) / 'sing-box'
    binary_path.write_text(
        '#!/usr/bin/env python3\n'
        'import json\n'
        'import pathlib\n'
        'import sys\n'
        'if sys.argv[1:] == ["version"]:\n'
        '    print("sing-box version 1.13.14-test")\n'
        '    raise SystemExit(0)\n'
        'if len(sys.argv) == 4 and sys.argv[1:3] == ["check", "-c"]:\n'
        '    json.loads(pathlib.Path(sys.argv[3]).read_text())\n'
        '    raise SystemExit(0)\n'
        'if len(sys.argv) == 6 and sys.argv[1:4] == ["rule-set", "compile", "--output"]:\n'
        '    json.loads(pathlib.Path(sys.argv[5]).read_text())\n'
        '    pathlib.Path(sys.argv[4]).write_bytes(b"srs")\n'
        '    raise SystemExit(0)\n'
        'raise SystemExit(2)\n',
        encoding='utf-8',
    )
    binary_path.chmod(0o755)
    binary_sha256 = hashlib.sha256(binary_path.read_bytes()).hexdigest()
    app = create_app(
        db_url=f'sqlite:///{db_path}',
        sing_box_binary=binary_path,
        sing_box_sha256=binary_sha256,
        sing_box_artifact_dir=artifact_dir,
    )
    with TestClient(app) as test_client:
        yield test_client


def _minimal_sing_box_template() -> dict[str, object]:
    return {
        'outbounds': [
            {'$csm': 'node_outbounds'},
            {'type': 'selector', 'tag': 'proxy', 'outbounds': [{'$csm': 'node_tags'}]},
            {'type': 'direct', 'tag': 'direct'},
        ],
        'route': {
            'rule_set': [{'$csm': 'rule_sets', 'sources': []}],
            'rules': [],
            'final': 'proxy',
        },
    }


def _create_sing_box_target(
    client: TestClient,
    *,
    name: str,
    subscription_content: str,
    template_document: dict[str, object],
) -> dict[str, object]:
    subscription = client.post(
        '/subscriptions',
        json={'name': f'{name}-subscription', 'content': subscription_content},
    ).json()
    template = client.post(
        '/templates',
        json={
            'name': f'{name}-template',
            'content': json.dumps(template_document),
            'target': 'sing-box',
            'schema_version': '1.13',
            'format': 'json',
        },
    ).json()
    profile = client.post(
        '/merge-profiles',
        json={'name': name, 'subscription_ids': [subscription['id']]},
    ).json()
    response = client.put(
        f'/merge-profiles/{profile["id"]}/targets/sing-box',
        json={'compatibility_version': '1.13.14', 'template_id': template['id']},
    )
    assert response.status_code == 200
    return profile


def test_convert_endpoint_returns_clash_config(client: TestClient) -> None:
    response = client.post(
        '/convert',
        json={'content': 'trojan://secret@example.com:443#Demo'},
    )

    assert response.status_code == 200
    rendered = yaml.safe_load(response.json()['content'])
    assert rendered['proxies'][0]['name'] == 'Demo'
    assert rendered['proxy-groups'][0]['proxies'] == ['Demo', 'DIRECT']


def test_merge_endpoint_merges_multiple_sources(client: TestClient) -> None:
    response = client.post(
        '/merge',
        json={
            'configs': [
                {'content': 'trojan://secret@example.com:443#One'},
                {'content': 'trojan://another@example.com:443#Two'},
            ]
        },
    )

    assert response.status_code == 200
    rendered = yaml.safe_load(response.json()['content'])
    assert [proxy['name'] for proxy in rendered['proxies']] == ['One', 'Two']
    assert rendered['proxy-groups'][0]['proxies'] == ['One', 'Two', 'DIRECT']


def test_subscription_crud_endpoints(client: TestClient) -> None:
    create_response = client.post(
        '/subscriptions',
        json={'name': 'demo', 'content': 'trojan://secret@example.com:443#Demo'},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created['timeout_seconds'] == 5.0

    list_response = client.get('/subscriptions')
    assert list_response.status_code == 200
    assert list_response.json()[0]['name'] == 'demo'

    update_response = client.put(
        f'/subscriptions/{created["id"]}',
        json={'enabled': False, 'timeout_seconds': 12.5},
    )
    assert update_response.status_code == 200
    assert update_response.json()['enabled'] is False
    assert update_response.json()['timeout_seconds'] == 12.5

    invalid_timeout_response = client.put(
        f'/subscriptions/{created["id"]}',
        json={'timeout_seconds': 0},
    )
    assert invalid_timeout_response.status_code == 422
    assert client.get(f'/subscriptions/{created["id"]}').json()['timeout_seconds'] == 12.5

    delete_response = client.delete(f'/subscriptions/{created["id"]}')
    assert delete_response.status_code == 204


def test_subscription_manual_update_records_timestamp_and_cache(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    async def fake_fetch(self: SubscriptionFetcher) -> str:
        nonlocal calls
        if self.config.content is not None:
            return self.config.content
        calls += 1
        if calls == 1:
            return 'trojan://secret@example.com:443#Manual'
        message = 'network down'
        raise SubscriptionFetchError(message)

    monkeypatch.setattr(SubscriptionFetcher, 'fetch', fake_fetch)

    subscription_response = client.post(
        '/subscriptions',
        json={'name': 'remote', 'url': 'https://example.com/sub'},
    )
    assert subscription_response.status_code == 201
    subscription = subscription_response.json()
    assert subscription['last_updated_at'] is None

    refresh_response = client.post(f'/subscriptions/{subscription["id"]}/update')
    assert refresh_response.status_code == 200
    refreshed = refresh_response.json()
    assert refreshed['last_updated_at'] is not None

    profile_response = client.post(
        '/merge-profiles',
        json={
            'name': 'manual-cache-profile',
            'subscription_ids': [subscription['id']],
        },
    )
    assert profile_response.status_code == 201
    generate_response = client.post(f'/merge-profiles/{profile_response.json()["id"]}/generate')
    assert generate_response.status_code == 200
    rendered = yaml.safe_load(generate_response.json()['content'])
    assert [proxy['name'] for proxy in rendered['proxies']] == ['Manual']
    assert calls == 2


def test_subscription_manual_update_rejects_unparseable_content(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_fetch(self: SubscriptionFetcher) -> str:
        if self.config.content is not None:
            return self.config.content
        return 'vless://12345678-1234-1234-1234-1234567890ab@example.com:443#不支持节点'

    monkeypatch.setattr(SubscriptionFetcher, 'fetch', fake_fetch)

    subscription_response = client.post(
        '/subscriptions',
        json={'name': 'remote-invalid', 'url': 'https://example.com/sub'},
    )
    assert subscription_response.status_code == 201
    subscription = subscription_response.json()

    refresh_response = client.post(f'/subscriptions/{subscription["id"]}/update')

    assert refresh_response.status_code == 422
    assert refresh_response.json()['detail'].startswith('unsupported proxy scheme: vless://')
    assert client.get(f'/subscriptions/{subscription["id"]}').json()['last_updated_at'] is None


def test_template_and_rule_source_endpoints(client: TestClient) -> None:
    template_response = client.post(
        '/templates',
        json={'name': 'default', 'content': 'proxies: []', 'is_default': True},
    )
    assert template_response.status_code == 201
    assert template_response.json()['name'] == 'default'

    rule_source_response = client.post(
        '/rule-sources',
        json={'name': 'rules', 'url': 'https://example.com/rules.txt'},
    )
    assert rule_source_response.status_code == 201

    list_response = client.get('/rule-sources')
    assert list_response.status_code == 200
    assert list_response.json()[0]['name'] == 'rules'


def test_named_resources_require_non_blank_name(client: TestClient) -> None:
    subscription_response = client.post(
        '/subscriptions',
        json={'name': '   ', 'content': 'trojan://secret@example.com:443#Demo'},
    )
    assert subscription_response.status_code == 422

    rule_source_response = client.post(
        '/rule-sources',
        json={'name': '   ', 'url': 'https://example.com/rules.txt'},
    )
    assert rule_source_response.status_code == 422


def test_duplicate_name_errors_are_friendly(client: TestClient) -> None:
    first_subscription = client.post(
        '/subscriptions',
        json={'name': 'demo', 'content': 'trojan://secret@example.com:443#Demo'},
    )
    assert first_subscription.status_code == 201

    duplicate_subscription = client.post(
        '/subscriptions',
        json={'name': 'demo', 'content': 'trojan://another@example.com:443#Demo'},
    )
    assert duplicate_subscription.status_code == 409
    assert duplicate_subscription.json() == {'detail': 'subscription name already exists'}

    first_rule_source = client.post(
        '/rule-sources',
        json={'name': 'rules', 'url': 'https://example.com/rules.txt'},
    )
    assert first_rule_source.status_code == 201

    duplicate_rule_source = client.post(
        '/rule-sources',
        json={'name': 'rules', 'url': 'https://example.com/other-rules.txt'},
    )
    assert duplicate_rule_source.status_code == 409
    assert duplicate_rule_source.json() == {'detail': 'rule source name already exists'}


def test_mihomo_profile_keeps_legacy_config_url_with_target_metadata(client: TestClient) -> None:
    subscription = client.post(
        '/subscriptions',
        json={'name': 'legacy-subscription', 'content': 'trojan://secret@example.com:443#Legacy'},
    ).json()
    template_response = client.post(
        '/templates',
        json={'name': 'legacy-template', 'content': 'rules:\n  - MATCH,DIRECT'},
    )
    assert template_response.status_code == 201
    template = template_response.json()
    assert template['target'] == 'mihomo'
    assert template['schema_version'] == '1'
    assert template['format'] == 'yaml'

    profile_response = client.post(
        '/merge-profiles',
        json={
            'name': 'legacy-profile',
            'template_source': {'kind': 'template', 'id': template['id']},
            'subscription_ids': [subscription['id']],
        },
    )
    assert profile_response.status_code == 201
    profile = profile_response.json()
    assert profile['public_id']

    config_response = client.get('/merge-profiles/by-name/legacy-profile/config')
    assert config_response.status_code == 200
    assert yaml.safe_load(config_response.text)['proxies'][0]['name'] == 'Legacy'


def test_sing_box_target_rejects_target_version_and_template_mismatches(client: TestClient) -> None:
    subscription = client.post(
        '/subscriptions',
        json={'name': 'target-subscription', 'content': 'trojan://secret@example.com:443#Target'},
    ).json()
    profile = client.post(
        '/merge-profiles',
        json={'name': 'target-profile', 'subscription_ids': [subscription['id']]},
    ).json()
    mihomo_template = client.post(
        '/templates',
        json={'name': 'mihomo-only', 'content': 'rules:\n  - MATCH,DIRECT'},
    ).json()
    sing_box_template = client.post(
        '/templates',
        json={
            'name': 'sing-box-template',
            'content': '{}',
            'target': 'sing-box',
            'schema_version': '1.13',
            'format': 'json',
        },
    ).json()

    wrong_template = client.put(
        f'/merge-profiles/{profile["id"]}/targets/sing-box',
        json={'compatibility_version': '1.13.14', 'template_id': mihomo_template['id']},
    )
    assert wrong_template.status_code == 422
    assert wrong_template.json() == {'detail': 'template target must be sing-box'}

    wrong_version = client.put(
        f'/merge-profiles/{profile["id"]}/targets/sing-box',
        json={'compatibility_version': '1.12.0', 'template_id': sing_box_template['id']},
    )
    assert wrong_version.status_code == 422
    assert wrong_version.json() == {'detail': 'sing-box compatibility version must be 1.13.14'}


def test_template_target_metadata_must_be_coherent(client: TestClient) -> None:
    response = client.post(
        '/templates',
        json={
            'name': 'invalid-sing-box-template',
            'content': '{}',
            'target': 'sing-box',
            'schema_version': '1.12',
            'format': 'json',
        },
    )

    assert response.status_code == 422
    assert response.json()['detail'][0]['msg'].endswith(
        'sing-box templates require schema_version 1.13 and format json'
    )


def test_sing_box_templates_cannot_use_composites(client: TestClient) -> None:
    template = client.post(
        '/templates',
        json={
            'name': 'sing-box-no-patches',
            'content': '{}',
            'target': 'sing-box',
            'schema_version': '1.13',
            'format': 'json',
        },
    ).json()

    response = client.post(
        '/composite-templates',
        json={'name': 'invalid-sing-box-composite', 'base_template_id': template['id'], 'patch_sequence': []},
    )

    assert response.status_code == 422
    assert response.json() == {'detail': 'sing-box templates do not support patches or composites'}


def test_sing_box_target_returns_valid_complete_json(sing_box_client: TestClient) -> None:
    rule_source = sing_box_client.post(
        '/rule-sources',
        json={
            'name': 'domains',
            'url': 'https://example.com/domains.txt',
            'auto_update': False,
            'content': "payload:\n  - '+.example.com'\n",
        },
    ).json()
    assert rule_source['name'] == 'domains'
    subscription = sing_box_client.post(
        '/subscriptions',
        json={
            'name': 'sing-box-nodes',
            'content': (
                'proxies:\n'
                '  - name: SS Obfs\n'
                '    type: ss\n'
                '    server: ss.example.com\n'
                '    port: 8388\n'
                '    cipher: aes-128-gcm\n'
                '    password: ss-secret\n'
                '    plugin: obfs\n'
                '    plugin-opts:\n'
                '      mode: http\n'
                '      host: www.example.com\n'
                '  - name: Trojan Secure\n'
                '    type: trojan\n'
                '    server: trojan.example.com\n'
                '    port: 443\n'
                '    password: trojan-secret\n'
                '    sni: edge.example.com\n'
                '    skip-cert-verify: true\n'
                '  - name: AnyTLS\n'
                '    type: anytls\n'
                '    server: anytls.example.com\n'
                '    port: 443\n'
                '    password: anytls-secret\n'
            ),
        },
    ).json()
    template_document = {
        'log': {'level': 'warn'},
        'dns': {
            'servers': [
                {'type': 'udp', 'tag': 'dns-local', 'server': '223.5.5.5', 'server_port': 53},
            ]
        },
        'inbounds': [
            {
                'type': 'tun',
                'tag': 'tun-in',
                'address': ['172.19.0.1/30', 'fdfe:dcba:9876::1/126'],
                'auto_route': True,
                'strict_route': True,
            }
        ],
        'outbounds': [
            {'$csm': 'node_outbounds'},
            {'type': 'selector', 'tag': 'proxy', 'outbounds': [{'$csm': 'node_tags'}]},
            {'type': 'direct', 'tag': 'direct'},
        ],
        'route': {
            'rule_set': [
                {
                    '$csm': 'rule_sets',
                    'sources': [{'source': 'domains', 'tag': 'domains', 'behavior': 'domain'}],
                }
            ],
            'rules': [{'rule_set': ['domains'], 'action': 'route', 'outbound': 'proxy'}],
            'final': 'proxy',
            'auto_detect_interface': True,
        },
    }
    template = sing_box_client.post(
        '/templates',
        json={
            'name': 'native-sing-box',
            'content': json.dumps(template_document),
            'target': 'sing-box',
            'schema_version': '1.13',
            'format': 'json',
        },
    ).json()
    profile = sing_box_client.post(
        '/merge-profiles',
        json={'name': 'sing-box-profile', 'subscription_ids': [subscription['id']]},
    ).json()
    binding_response = sing_box_client.put(
        f'/merge-profiles/{profile["id"]}/targets/sing-box',
        json={'compatibility_version': '1.13.14', 'template_id': template['id']},
    )
    assert binding_response.status_code == 200

    config_response = sing_box_client.get(
        f'/api/v1/merge-profiles/{profile["public_id"]}/targets/sing-box/config.json',
        params={'compat': '1.13.14'},
    )
    assert config_response.status_code == 200
    assert config_response.headers['content-type'].startswith('application/json')
    assert config_response.headers['x-csm-warning-count'] == '1'
    config = config_response.json()
    node_outbounds = [outbound for outbound in config['outbounds'] if outbound['type'] not in {'selector', 'direct'}]
    assert [outbound['tag'] for outbound in node_outbounds] == ['SS Obfs', 'Trojan Secure', 'AnyTLS']
    assert node_outbounds[0]['plugin'] == 'obfs-local'
    assert node_outbounds[0]['plugin_opts'] == 'obfs=http;obfs-host=www.example.com'
    assert node_outbounds[1]['tls']['insecure'] is True
    selector = next(outbound for outbound in config['outbounds'] if outbound['type'] == 'selector')
    assert selector['outbounds'] == ['SS Obfs', 'Trojan Secure', 'AnyTLS']
    rule_set = config['route']['rule_set'][0]
    assert rule_set['format'] == 'source'
    assert rule_set['url'].startswith('http://testserver/api/v1/sing-box/rule-sets/v4/')

    rule_set_response = sing_box_client.get(rule_set['url'])
    assert rule_set_response.status_code == 200
    assert rule_set_response.json() == {'version': 4, 'rules': [{'domain_suffix': ['example.com']}]}


def test_sing_box_client_pull_uses_cached_subscription(
    sing_box_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    async def fake_fetch(self: SubscriptionFetcher) -> str:
        nonlocal calls
        if self.config.content is not None:
            return self.config.content
        calls += 1
        return 'trojan://secret@example.com:443#Cached'

    monkeypatch.setattr(SubscriptionFetcher, 'fetch', fake_fetch)
    subscription = sing_box_client.post(
        '/subscriptions',
        json={'name': 'remote-sing-box', 'url': 'https://example.com/sub'},
    ).json()
    refresh_response = sing_box_client.post(f'/subscriptions/{subscription["id"]}/update')
    assert refresh_response.status_code == 200
    assert calls == 1

    template = sing_box_client.post(
        '/templates',
        json={
            'name': 'cached-sing-box-template',
            'content': json.dumps(_minimal_sing_box_template()),
            'target': 'sing-box',
            'schema_version': '1.13',
            'format': 'json',
        },
    ).json()
    profile = sing_box_client.post(
        '/merge-profiles',
        json={'name': 'cached-sing-box-profile', 'subscription_ids': [subscription['id']]},
    ).json()
    binding_response = sing_box_client.put(
        f'/merge-profiles/{profile["id"]}/targets/sing-box',
        json={'compatibility_version': '1.13.14', 'template_id': template['id']},
    )
    assert binding_response.status_code == 200

    config_response = sing_box_client.get(
        f'/api/v1/merge-profiles/{profile["public_id"]}/targets/sing-box/config.json',
        params={'compat': '1.13.14'},
    )

    assert config_response.status_code == 200
    node_outbounds = [
        outbound for outbound in config_response.json()['outbounds'] if outbound['type'] not in {'selector', 'direct'}
    ]
    assert [outbound['tag'] for outbound in node_outbounds] == ['Cached']
    assert calls == 1


def test_exact_subscription_node_exclusions_apply_to_both_targets(sing_box_client: TestClient) -> None:
    subscription = sing_box_client.post(
        '/subscriptions',
        json={
            'name': 'filtered-subscription',
            'content': (
                'proxies:\n'
                "  - name: 'Traffic: 1 GB'\n"
                '    type: trojan\n'
                '    server: metadata.example.com\n'
                '    port: 443\n'
                '    password: metadata\n'
                '  - name: Real Node\n'
                '    type: trojan\n'
                '    server: real.example.com\n'
                '    port: 443\n'
                '    password: real\n'
            ),
            'excluded_node_names': ['Traffic: 1 GB'],
        },
    ).json()
    assert subscription['excluded_node_names'] == ['Traffic: 1 GB']
    profile = sing_box_client.post(
        '/merge-profiles',
        json={'name': 'filtered-profile', 'subscription_ids': [subscription['id']]},
    ).json()

    mihomo_response = sing_box_client.get('/merge-profiles/by-name/filtered-profile/config')
    assert mihomo_response.status_code == 200
    assert [proxy['name'] for proxy in yaml.safe_load(mihomo_response.text)['proxies']] == ['Real Node']

    template = sing_box_client.post(
        '/templates',
        json={
            'name': 'filtered-sing-box-template',
            'content': json.dumps(_minimal_sing_box_template()),
            'target': 'sing-box',
            'schema_version': '1.13',
            'format': 'json',
        },
    ).json()
    binding = sing_box_client.put(
        f'/merge-profiles/{profile["id"]}/targets/sing-box',
        json={'compatibility_version': '1.13.14', 'template_id': template['id']},
    )
    assert binding.status_code == 200

    sing_box_response = sing_box_client.get(
        f'/api/v1/merge-profiles/{profile["public_id"]}/targets/sing-box/config.json',
        params={'compat': '1.13.14'},
    )
    assert sing_box_response.status_code == 200
    assert sing_box_response.headers['x-csm-dropped-node-count'] == '1'
    node_outbounds = [
        outbound for outbound in sing_box_response.json()['outbounds'] if outbound['type'] not in {'selector', 'direct'}
    ]
    assert [outbound['tag'] for outbound in node_outbounds] == ['Real Node']


def test_sing_box_target_rejects_residual_markers(sing_box_client: TestClient) -> None:
    template_document = _minimal_sing_box_template()
    template_document['experimental'] = {'$csm': 'unknown'}
    profile = _create_sing_box_target(
        sing_box_client,
        name='invalid-marker-profile',
        subscription_content='trojan://secret@example.com:443#Marker',
        template_document=template_document,
    )

    response = sing_box_client.get(
        f'/api/v1/merge-profiles/{profile["public_id"]}/targets/sing-box/config.json',
        params={'compat': '1.13.14'},
    )

    assert response.status_code == 422
    assert response.json()['detail'] == 'unsupported or misplaced $csm marker at $.experimental'


@pytest.mark.parametrize(
    ('subscription_content', 'expected_detail'),
    [
        (
            (
                'proxies:\n'
                '  - name: VMess\n'
                '    type: vmess\n'
                '    server: vmess.example.com\n'
                '    port: 443\n'
                '    uuid: 00000000-0000-0000-0000-000000000001\n'
            ),
            'unsupported sing-box proxy node type: vmess',
        ),
        (
            (
                'proxies:\n'
                '  - name: Unsupported Plugin\n'
                '    type: ss\n'
                '    server: ss.example.com\n'
                '    port: 8388\n'
                '    cipher: aes-128-gcm\n'
                '    password: secret\n'
                '    plugin: v2ray-plugin\n'
            ),
            "unsupported shadowsocks plugin for 'Unsupported Plugin': v2ray-plugin",
        ),
    ],
)
def test_sing_box_target_rejects_unsupported_nodes_and_plugins(
    sing_box_client: TestClient,
    subscription_content: str,
    expected_detail: str,
) -> None:
    profile = _create_sing_box_target(
        sing_box_client,
        name=f'unsupported-{len(expected_detail)}',
        subscription_content=subscription_content,
        template_document=_minimal_sing_box_template(),
    )

    response = sing_box_client.get(
        f'/api/v1/merge-profiles/{profile["public_id"]}/targets/sing-box/config.json',
        params={'compat': '1.13.14'},
    )

    assert response.status_code == 422
    assert response.json()['detail'] == expected_detail


def test_sing_box_rule_set_digest_urls_are_immutable(sing_box_client: TestClient) -> None:
    rule_source = sing_box_client.post(
        '/rule-sources',
        json={
            'name': 'digest-rules',
            'url': 'https://example.com/digest-rules.txt',
            'auto_update': False,
            'content': "payload:\n  - '+.first.example'\n",
        },
    ).json()
    template_document = _minimal_sing_box_template()
    route = template_document['route']
    assert isinstance(route, dict)
    rule_sets = route['rule_set']
    assert isinstance(rule_sets, list) and isinstance(rule_sets[0], dict)
    rule_sets[0]['sources'] = [{'source': 'digest-rules', 'tag': 'digest-rules', 'behavior': 'domain'}]
    profile = _create_sing_box_target(
        sing_box_client,
        name='digest-profile',
        subscription_content='trojan://secret@example.com:443#Digest',
        template_document=template_document,
    )
    config_url = f'/api/v1/merge-profiles/{profile["public_id"]}/targets/sing-box/config.json'

    first_config = sing_box_client.get(config_url, params={'compat': '1.13.14'}).json()
    first_url = first_config['route']['rule_set'][0]['url']
    first_content = sing_box_client.get(first_url).json()

    update_response = sing_box_client.put(
        f'/rule-sources/{rule_source["id"]}',
        json={'content': "payload:\n  - '+.second.example'\n"},
    )
    assert update_response.status_code == 200
    second_config = sing_box_client.get(config_url, params={'compat': '1.13.14'}).json()
    second_url = second_config['route']['rule_set'][0]['url']

    assert first_url != second_url
    assert sing_box_client.get(first_url).json() == first_content
    assert sing_box_client.get(second_url).json() == {
        'version': 4,
        'rules': [{'domain_suffix': ['second.example']}],
    }


def test_merge_profile_crud_and_generate(client: TestClient) -> None:
    first_subscription = client.post(
        '/subscriptions',
        json={'name': 'alpha', 'content': 'trojan://secret@example.com:443#Alpha'},
    )
    second_subscription = client.post(
        '/subscriptions',
        json={'name': 'beta', 'content': 'trojan://secret2@example.com:443#Beta'},
    )
    rule_source_response = client.post(
        '/rule-sources',
        json={
            'name': 'applications',
            'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/applications.txt',
            'auto_update': False,
            'content': 'PROCESS-NAME,Word.exe,DIRECT\n',
        },
    )
    template_response = client.post(
        '/templates',
        json={
            'name': 'daily',
            'content': (
                'proxy-groups:\n'
                '  - name: Select\n'
                '    type: select\n'
                '    proxies:\n'
                '      - DIRECT\n'
                'rule-providers:\n'
                '  applications:\n'
                '    type: http\n'
                '    behavior: classical\n'
                '    url: https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/applications.txt\n'
                '    path: ./ruleset/applications.yaml\n'
                '    interval: 86400\n'
                'rules:\n'
                '  - RULE-SET,applications,Select\n'
                '  - MATCH,Select'
            ),
        },
    )
    assert first_subscription.status_code == 201
    assert second_subscription.status_code == 201
    assert rule_source_response.status_code == 201
    assert template_response.status_code == 201

    create_response = client.post(
        '/merge-profiles',
        json={
            'name': 'daily-profile',
            'template_source': {'kind': 'template', 'id': template_response.json()['id']},
            'subscription_ids': [first_subscription.json()['id'], second_subscription.json()['id']],
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created['name'] == 'daily-profile'
    assert created['template_source'] == {'id': template_response.json()['id'], 'name': 'daily', 'kind': 'template'}
    assert [subscription['name'] for subscription in created['subscriptions']] == ['alpha', 'beta']

    list_response = client.get('/merge-profiles')
    assert list_response.status_code == 200
    assert list_response.json()[0]['name'] == 'daily-profile'

    update_response = client.put(
        f'/merge-profiles/{created["id"]}',
        json={'name': 'travel-profile', 'enabled': False, 'subscription_ids': [second_subscription.json()['id']]},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated['name'] == 'travel-profile'
    assert updated['enabled'] is False
    assert [subscription['name'] for subscription in updated['subscriptions']] == ['beta']

    generate_response = client.post(f'/merge-profiles/{created["id"]}/generate')
    assert generate_response.status_code == 200
    generated = yaml.safe_load(generate_response.json()['content'])
    assert [proxy['name'] for proxy in generated['proxies']] == ['Beta']
    assert generated['proxy-groups'][0]['name'] == 'Select'
    assert generated['rules'] == ['RULE-SET,applications,Select', 'MATCH,Select']
    expected_provider_url = f'http://testserver/rule-providers/{rule_source_response.json()["id"]}'
    assert generated['rule-providers']['applications']['url'] == expected_provider_url

    config_response = client.get(f'/merge-profiles/by-name/{updated["name"]}/config')
    assert config_response.status_code == 200
    config_body = yaml.safe_load(config_response.text)
    assert [proxy['name'] for proxy in config_body['proxies']] == ['Beta']
    assert config_body['rule-providers']['applications']['url'] == expected_provider_url

    delete_response = client.delete(f'/merge-profiles/{created["id"]}')
    assert delete_response.status_code == 204


def test_merge_profile_uses_cached_subscription_when_remote_refresh_fails(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    async def fake_fetch(self: SubscriptionFetcher) -> str:
        nonlocal calls
        if self.config.content is not None:
            return self.config.content
        calls += 1
        if calls == 1:
            return 'trojan://secret@example.com:443#Cached'
        message = 'network down'
        raise SubscriptionFetchError(message)

    monkeypatch.setattr(SubscriptionFetcher, 'fetch', fake_fetch)

    subscription_response = client.post(
        '/subscriptions',
        json={'name': 'remote', 'url': 'https://example.com/sub'},
    )
    assert subscription_response.status_code == 201

    profile_response = client.post(
        '/merge-profiles',
        json={
            'name': 'cached-profile',
            'subscription_ids': [subscription_response.json()['id']],
        },
    )
    assert profile_response.status_code == 201
    profile_id = profile_response.json()['id']

    first_generate = client.post(f'/merge-profiles/{profile_id}/generate')
    assert first_generate.status_code == 200
    first_rendered = yaml.safe_load(first_generate.json()['content'])
    assert [proxy['name'] for proxy in first_rendered['proxies']] == ['Cached']

    client_pull = client.get('/merge-profiles/by-name/cached-profile/config')
    assert client_pull.status_code == 200
    pulled = yaml.safe_load(client_pull.text)
    assert [proxy['name'] for proxy in pulled['proxies']] == ['Cached']
    assert calls == 1

    try:
        second_generate = client.post(f'/merge-profiles/{profile_id}/generate')
    except SubscriptionFetchError:
        pytest.fail('expected cached subscription content to be used when refresh fails')

    assert second_generate.status_code == 200
    second_rendered = yaml.safe_load(second_generate.json()['content'])
    assert [proxy['name'] for proxy in second_rendered['proxies']] == ['Cached']
    assert calls == 2


def test_merge_profile_uses_cached_subscription_when_remote_refresh_is_empty(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    async def fake_fetch(self: SubscriptionFetcher) -> str:
        nonlocal calls
        if self.config.content is not None:
            return self.config.content
        calls += 1
        if calls == 1:
            return 'trojan://secret@example.com:443#Cached'
        return '  \n'

    monkeypatch.setattr(SubscriptionFetcher, 'fetch', fake_fetch)

    subscription_response = client.post(
        '/subscriptions',
        json={'name': 'remote-empty', 'url': 'https://example.com/sub'},
    )
    assert subscription_response.status_code == 201
    profile_response = client.post(
        '/merge-profiles',
        json={
            'name': 'cached-empty-profile',
            'subscription_ids': [subscription_response.json()['id']],
        },
    )
    assert profile_response.status_code == 201
    profile_id = profile_response.json()['id']

    first_generate = client.post(f'/merge-profiles/{profile_id}/generate')
    assert first_generate.status_code == 200

    second_generate = client.post(f'/merge-profiles/{profile_id}/generate')

    assert second_generate.status_code == 200
    rendered = yaml.safe_load(second_generate.json()['content'])
    assert [proxy['name'] for proxy in rendered['proxies']] == ['Cached']
    assert calls == 2


def test_merge_profile_rejects_empty_remote_subscription_content(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_fetch(self: SubscriptionFetcher) -> str:
        if self.config.content is not None:
            return self.config.content
        return '  \n'

    monkeypatch.setattr(SubscriptionFetcher, 'fetch', fake_fetch)

    subscription_response = client.post(
        '/subscriptions',
        json={'name': 'empty-remote', 'url': 'https://example.com/sub'},
    )
    assert subscription_response.status_code == 201
    profile_response = client.post(
        '/merge-profiles',
        json={
            'name': 'empty-profile',
            'subscription_ids': [subscription_response.json()['id']],
        },
    )
    assert profile_response.status_code == 201

    generate_response = client.post(f'/merge-profiles/{profile_response.json()["id"]}/generate')

    assert generate_response.status_code == 422
    assert generate_response.json() == {'detail': "subscription 'empty-remote' content must not be empty"}


def test_subscription_source_update_clears_cached_remote_content(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    async def fake_fetch(self: SubscriptionFetcher) -> str:
        nonlocal calls
        if self.config.content is not None:
            return self.config.content
        calls += 1
        if calls == 1:
            return 'trojan://secret@example.com:443#Old'
        message = 'network down'
        raise SubscriptionFetchError(message)

    monkeypatch.setattr(SubscriptionFetcher, 'fetch', fake_fetch)

    subscription_response = client.post(
        '/subscriptions',
        json={'name': 'remote', 'url': 'https://example.com/old-sub'},
    )
    assert subscription_response.status_code == 201
    subscription_id = subscription_response.json()['id']

    profile_response = client.post(
        '/merge-profiles',
        json={
            'name': 'stale-cache-profile',
            'subscription_ids': [subscription_id],
        },
    )
    assert profile_response.status_code == 201
    profile_id = profile_response.json()['id']

    first_generate = client.post(f'/merge-profiles/{profile_id}/generate')
    assert first_generate.status_code == 200

    update_response = client.put(
        f'/subscriptions/{subscription_id}',
        json={'url': 'https://example.com/new-sub'},
    )
    assert update_response.status_code == 200

    with pytest.raises(SubscriptionFetchError):
        client.post(f'/merge-profiles/{profile_id}/generate')
    assert calls == 2


def test_merge_profile_accepts_composite_template(client: TestClient) -> None:
    subscription_response = client.post(
        '/subscriptions',
        json={'name': 'beta', 'content': 'trojan://secret2@example.com:443#Beta'},
    )
    template_response = client.post(
        '/templates',
        json={
            'name': 'daily',
            'content': (
                'proxy-groups:\n'
                '  - name: Select\n'
                '    type: select\n'
                '    proxies:\n'
                '      - DIRECT\n'
                'rules:\n'
                '  - MATCH,Select'
            ),
        },
    )
    patch_response = client.post(
        '/template-patches',
        json={
            'name': 'append-beta',
            'operations': [
                {'op': 'list_insert', 'path': 'proxy-groups.0.proxies', 'index': 0, 'value': 'Beta'},
            ],
        },
    )
    assert subscription_response.status_code == 201
    assert template_response.status_code == 201
    assert patch_response.status_code == 201

    composite_response = client.post(
        '/composite-templates',
        json={
            'name': 'derived-select',
            'base_template_id': template_response.json()['id'],
            'patch_sequence': [patch_response.json()['id']],
        },
    )
    assert composite_response.status_code == 201
    composite_id = composite_response.json()['id']

    profile_response = client.post(
        '/merge-profiles',
        json={
            'name': 'composite-profile',
            'template_source': {'kind': 'composite', 'id': composite_id},
            'subscription_ids': [subscription_response.json()['id']],
        },
    )
    assert profile_response.status_code == 201
    created_profile = profile_response.json()
    assert created_profile['template_source'] == {'id': composite_id, 'name': 'derived-select', 'kind': 'composite'}

    generated_response = client.post(f'/merge-profiles/{created_profile["id"]}/generate')
    assert generated_response.status_code == 200
    generated = yaml.safe_load(generated_response.json()['content'])
    assert generated['proxy-groups'][0]['proxies'][0] == 'Beta'

    blocked_delete = client.delete(f'/composite-templates/{composite_id}')
    assert blocked_delete.status_code == 409
    assert blocked_delete.json() == {'detail': 'composite template is used by merge profile: composite-profile'}


def test_template_patch_and_composite_template_endpoints(client: TestClient) -> None:
    template_response = client.post(
        '/templates',
        json={
            'name': 'base-template',
            'content': ('proxy-groups:\n  - name: Auto\n    proxies:\n      - DIRECT\n'),
        },
    )
    assert template_response.status_code == 201
    template_id = template_response.json()['id']

    append_patch_response = client.post(
        '/template-patches',
        json={
            'name': 'append-node',
            'operations': [
                {'op': 'list_append', 'path': 'proxy-groups.0.proxies', 'value': 'Node-A'},
            ],
        },
    )
    assert append_patch_response.status_code == 201
    append_patch_id = append_patch_response.json()['id']

    replace_patch_response = client.post(
        '/template-patches',
        json={
            'name': 'replace-node',
            'operations': [
                {
                    'op': 'list_replace',
                    'path': 'proxy-groups.0.proxies',
                    'index': 1,
                    'old_value': 'Node-A',
                    'value': 'Node-B',
                }
            ],
        },
    )
    assert replace_patch_response.status_code == 201
    replace_patch_id = replace_patch_response.json()['id']

    patch_preview = client.post(
        f'/template-patches/{append_patch_id}/preview',
        json={'base_template_id': template_id},
    )
    assert patch_preview.status_code == 200
    assert yaml.safe_load(patch_preview.json()['content'])['proxy-groups'][0]['proxies'] == ['DIRECT', 'Node-A']

    composite_preview = client.post(
        '/composite-templates/preview',
        json={'base_template_id': template_id, 'patch_sequence': [append_patch_id, replace_patch_id]},
    )
    assert composite_preview.status_code == 200
    assert yaml.safe_load(composite_preview.json()['content'])['proxy-groups'][0]['proxies'] == ['DIRECT', 'Node-B']

    composite_create = client.post(
        '/composite-templates',
        json={
            'name': 'derived-template',
            'base_template_id': template_id,
            'patch_sequence': [append_patch_id, replace_patch_id],
        },
    )
    assert composite_create.status_code == 201
    created_composite = composite_create.json()
    assert [patch['name'] for patch in created_composite['patches']] == ['append-node', 'replace-node']
    assert yaml.safe_load(created_composite['cached_content'])['proxy-groups'][0]['proxies'] == ['DIRECT', 'Node-B']

    blocked_template_delete = client.delete(f'/templates/{template_id}')
    assert blocked_template_delete.status_code == 409
    assert blocked_template_delete.json() == {'detail': 'template is used by a composite template'}

    blocked_patch_delete = client.delete(f'/template-patches/{append_patch_id}')
    assert blocked_patch_delete.status_code == 409
    assert blocked_patch_delete.json() == {'detail': 'template patch is used by composite templates: derived-template'}

    composite_update = client.put(
        f'/composite-templates/{created_composite["id"]}',
        json={'name': 'derived-template-v2', 'patch_sequence': [append_patch_id]},
    )
    assert composite_update.status_code == 200
    updated_composite = composite_update.json()
    assert updated_composite['name'] == 'derived-template-v2'
    assert yaml.safe_load(updated_composite['cached_content'])['proxy-groups'][0]['proxies'] == ['DIRECT', 'Node-A']

    composite_delete = client.delete(f'/composite-templates/{created_composite["id"]}')
    assert composite_delete.status_code == 204

    delete_replace_patch = client.delete(f'/template-patches/{replace_patch_id}')
    assert delete_replace_patch.status_code == 204
    delete_append_patch = client.delete(f'/template-patches/{append_patch_id}')
    assert delete_append_patch.status_code == 204

    delete_template = client.delete(f'/templates/{template_id}')
    assert delete_template.status_code == 204


def test_template_patch_list_remove_requires_index_and_supports_old_value(client: TestClient) -> None:
    template_response = client.post(
        '/templates',
        json={
            'name': 'remove-template',
            'content': (
                'proxy-groups:\n  - name: Auto\n    proxies:\n      - DIRECT\n      - Node-A\n      - Node-B\n'
            ),
        },
    )
    assert template_response.status_code == 201
    template_id = template_response.json()['id']

    invalid_patch_response = client.post(
        '/template-patches',
        json={
            'name': 'invalid-remove',
            'operations': [
                {'op': 'list_remove', 'path': 'proxy-groups.0.proxies', 'value': 'Node-A'},
            ],
        },
    )
    assert invalid_patch_response.status_code == 422

    remove_patch_response = client.post(
        '/template-patches',
        json={
            'name': 'remove-node',
            'operations': [
                {
                    'op': 'list_remove',
                    'path': 'proxy-groups.0.proxies',
                    'index': 1,
                    'old_value': 'Node-A',
                }
            ],
        },
    )
    assert remove_patch_response.status_code == 201
    remove_patch_id = remove_patch_response.json()['id']

    patch_preview = client.post(
        f'/template-patches/{remove_patch_id}/preview',
        json={'base_template_id': template_id},
    )
    assert patch_preview.status_code == 200
    assert yaml.safe_load(patch_preview.json()['content'])['proxy-groups'][0]['proxies'] == ['DIRECT', 'Node-B']
