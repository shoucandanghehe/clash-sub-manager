import pathlib
from collections.abc import Iterator

import pytest
import yaml
from fastapi.testclient import TestClient

from clash_sub_manager.api import create_app


@pytest.fixture
def client(tmp_path: pathlib.Path) -> Iterator[TestClient]:
    db_path = pathlib.Path(tmp_path) / 'api.db'
    app = create_app(db_url=f'sqlite:///{db_path}')
    with TestClient(app) as test_client:
        yield test_client


def test_convert_endpoint_returns_clash_config(client: TestClient) -> None:
    response = client.post(
        '/convert',
        json={'content': 'trojan://secret@example.com:443#Demo'},
    )

    assert response.status_code == 200
    body = response.json()
    assert body['proxies'][0]['name'] == 'Demo'
    assert body['proxy-groups'][0]['proxies'] == ['Demo', 'DIRECT']


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
    body = response.json()
    assert [proxy['name'] for proxy in body['proxies']] == ['One', 'Two']


def test_subscription_crud_endpoints(client: TestClient) -> None:
    create_response = client.post(
        '/subscriptions',
        json={'name': 'demo', 'content': 'trojan://secret@example.com:443#Demo'},
    )
    assert create_response.status_code == 201
    created = create_response.json()

    list_response = client.get('/subscriptions')
    assert list_response.status_code == 200
    assert list_response.json()[0]['name'] == 'demo'

    update_response = client.put(
        f"/subscriptions/{created['id']}",
        json={'enabled': False},
    )
    assert update_response.status_code == 200
    assert update_response.json()['enabled'] is False

    delete_response = client.delete(f"/subscriptions/{created['id']}")
    assert delete_response.status_code == 204


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
            'template_id': template_response.json()['id'],
            'subscription_ids': [first_subscription.json()['id'], second_subscription.json()['id']],
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created['name'] == 'daily-profile'
    assert created['template']['name'] == 'daily'
    assert [subscription['name'] for subscription in created['subscriptions']] == ['alpha', 'beta']

    list_response = client.get('/merge-profiles')
    assert list_response.status_code == 200
    assert list_response.json()[0]['name'] == 'daily-profile'

    update_response = client.put(
        f"/merge-profiles/{created['id']}",
        json={'name': 'travel-profile', 'enabled': False, 'subscription_ids': [second_subscription.json()['id']]},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated['name'] == 'travel-profile'
    assert updated['enabled'] is False
    assert [subscription['name'] for subscription in updated['subscriptions']] == ['beta']

    generate_response = client.post(f"/merge-profiles/{created['id']}/generate")
    assert generate_response.status_code == 200
    generated = generate_response.json()
    assert [proxy['name'] for proxy in generated['proxies']] == ['Beta']
    assert generated['proxy-groups'][0]['name'] == 'Select'
    assert generated['rules'] == ['RULE-SET,applications,Select', 'MATCH,Select']
    expected_provider_url = f"http://testserver/rule-providers/{rule_source_response.json()['id']}"
    assert generated['rule-providers']['applications']['url'] == expected_provider_url

    config_response = client.get(f"/merge-profiles/by-name/{updated['name']}/config")
    assert config_response.status_code == 200
    config_body = yaml.safe_load(config_response.text)
    assert [proxy['name'] for proxy in config_body['proxies']] == ['Beta']
    assert config_body['rule-providers']['applications']['url'] == expected_provider_url

    delete_response = client.delete(f"/merge-profiles/{created['id']}")
    assert delete_response.status_code == 204


def test_template_patch_and_composite_template_endpoints(client: TestClient) -> None:
    template_response = client.post(
        '/templates',
        json={
            'name': 'base-template',
            'content': (
                'proxy-groups:\n'
                '  - name: Auto\n'
                '    proxies:\n'
                '      - DIRECT\n'
            ),
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
    assert patch_preview.json()['content']['proxy-groups'][0]['proxies'] == ['DIRECT', 'Node-A']

    composite_preview = client.post(
        '/composite-templates/preview',
        json={'base_template_id': template_id, 'patch_sequence': [append_patch_id, replace_patch_id]},
    )
    assert composite_preview.status_code == 200
    assert composite_preview.json()['content']['proxy-groups'][0]['proxies'] == ['DIRECT', 'Node-B']

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
        f"/composite-templates/{created_composite['id']}",
        json={'name': 'derived-template-v2', 'patch_sequence': [append_patch_id]},
    )
    assert composite_update.status_code == 200
    updated_composite = composite_update.json()
    assert updated_composite['name'] == 'derived-template-v2'
    assert yaml.safe_load(updated_composite['cached_content'])['proxy-groups'][0]['proxies'] == ['DIRECT', 'Node-A']

    composite_delete = client.delete(f"/composite-templates/{created_composite['id']}")
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
                'proxy-groups:\n'
                '  - name: Auto\n'
                '    proxies:\n'
                '      - DIRECT\n'
                '      - Node-A\n'
                '      - Node-B\n'
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
    assert patch_preview.json()['content']['proxy-groups'][0]['proxies'] == ['DIRECT', 'Node-B']