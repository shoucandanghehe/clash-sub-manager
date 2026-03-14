from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from clash_sub_manager.models import ClashConfig, ProxyNodeModel, SubscriptionConfig


def test_proxy_union_uses_type_discriminator() -> None:
    adapter = TypeAdapter[ProxyNodeModel](ProxyNodeModel)
    node = adapter.validate_python(
        {
            'type': 'vmess',
            'name': 'demo',
            'server': 'example.com',
            'port': 443,
            'uuid': '12345678-1234-1234-1234-1234567890ab',
            'tls': True,
            'network': 'ws',
            'ws_headers': {'Host': 'edge.example.com'},
        }
    )

    assert node.type == 'vmess'
    assert node.ws_headers == {'Host': 'edge.example.com'}


def test_subscription_requires_exactly_one_source() -> None:
    with pytest.raises(ValidationError, match='exactly one of url or content'):
        SubscriptionConfig.model_validate({'name': 'invalid', 'url': 'https://example.com/sub', 'content': 'ss://abc'})

    with pytest.raises(ValidationError, match='exactly one of url or content'):
        SubscriptionConfig(name='invalid', content='   ')


def test_clash_config_uses_aliases_when_dumping() -> None:
    config = ClashConfig.model_validate(
        {'proxy-groups': [{'name': 'Auto', 'type': 'select', 'proxies': ['demo']}]},
    )

    dumped = config.model_dump(by_alias=True)
    expected_mixed_port = 7892

    assert dumped['proxy-groups'][0]['name'] == 'Auto'
    assert dumped['mixed-port'] == expected_mixed_port
