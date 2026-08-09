"""Domain models for supported proxy protocols."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProxyNode(BaseModel):
    """Common fields shared by every supported proxy node."""

    model_config = ConfigDict(extra='forbid')

    name: str
    server: str
    port: int = Field(ge=1, le=65535)

    @field_validator('name', 'server')
    @classmethod
    def validate_non_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            msg = 'value must not be blank'
            raise ValueError(msg)
        return stripped


class ShadowsocksNode(ProxyNode):
    type: Literal['ss'] = 'ss'
    cipher: str
    password: str
    udp: bool = True
    plugin: str | None = None
    plugin_opts: dict[str, str] | None = None


class ShadowsocksRNode(ProxyNode):
    type: Literal['ssr'] = 'ssr'
    cipher: str
    password: str
    protocol: str
    protocol_param: str | None = None
    obfs: str
    obfs_param: str | None = None
    udp: bool = True


class VMessNode(ProxyNode):
    type: Literal['vmess'] = 'vmess'
    uuid: str
    alter_id: int = Field(default=0, ge=0)
    cipher: str = 'auto'
    udp: bool = True
    tls: bool = False
    skip_cert_verify: bool = False
    servername: str | None = None
    network: Literal['tcp', 'ws', 'grpc'] = 'tcp'
    ws_path: str | None = None
    ws_headers: dict[str, str] = Field(default_factory=dict)
    grpc_service_name: str | None = None


class TrojanNode(ProxyNode):
    type: Literal['trojan'] = 'trojan'
    password: str
    udp: bool = True
    sni: str | None = None
    skip_cert_verify: bool = False
    network: Literal['tcp', 'ws', 'grpc'] = 'tcp'
    ws_path: str | None = None
    ws_headers: dict[str, str] = Field(default_factory=dict)
    grpc_service_name: str | None = None


class AnyTLSNode(ProxyNode):
    type: Literal['anytls'] = 'anytls'
    password: str
    udp: bool = True
    sni: str | None = None
    skip_cert_verify: bool = False
    client_fingerprint: str | None = None
    alpn: list[str] | None = None
    idle_session_check_interval: int | None = Field(default=None, ge=0)
    idle_session_timeout: int | None = Field(default=None, ge=0)
    min_idle_session: int | None = Field(default=None, ge=0)
    tfo: bool = False


class Hysteria2Node(ProxyNode):
    type: Literal['hysteria2'] = 'hysteria2'
    password: str
    udp: bool = True
    ports: str | int | None = None
    hop_interval: str | int | None = None
    up: str | int | None = None
    down: str | int | None = None
    bbr_profile: str | None = None
    obfs: str | None = None
    obfs_password: str | None = None
    obfs_min_packet_size: int | None = Field(default=None, ge=0)
    obfs_max_packet_size: int | None = Field(default=None, ge=0)
    sni: str | None = None
    skip_cert_verify: bool = False
    name_cert_verify: str | None = None
    fingerprint: str | None = None
    alpn: list[str] | None = None
    ech_config: str | None = None
    realm_opts: dict[str, object] | None = None
    initial_stream_receive_window: int | None = Field(default=None, ge=0)
    max_stream_receive_window: int | None = Field(default=None, ge=0)
    initial_connection_receive_window: int | None = Field(default=None, ge=0)
    max_connection_receive_window: int | None = Field(default=None, ge=0)


ProxyNodeModel = Annotated[
    ShadowsocksNode | ShadowsocksRNode | VMessNode | TrojanNode | AnyTLSNode | Hysteria2Node,
    Field(discriminator='type'),
]

__all__ = [
    'AnyTLSNode',
    'Hysteria2Node',
    'ProxyNode',
    'ProxyNodeModel',
    'ShadowsocksNode',
    'ShadowsocksRNode',
    'TrojanNode',
    'VMessNode',
]
