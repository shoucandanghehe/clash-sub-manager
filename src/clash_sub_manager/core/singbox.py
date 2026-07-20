"""Strict sing-box 1.13 configuration rendering and publication."""

import csv
import hashlib
import ipaddress
import json
import os
import subprocess
import tempfile
import threading
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, NoReturn, cast

import yaml

from ..models.proxy import AnyTLSNode, ProxyNodeModel, ShadowsocksNode, TrojanNode

SING_BOX_COMPATIBILITY_VERSION = '1.13.14'
SING_BOX_SCHEMA_VERSION = '1.13'
RULE_SET_VERSION = 4
_RULE_BEHAVIORS = frozenset({'classical', 'domain', 'ipcidr'})
_RULE_FIELDS = ('domain', 'domain_suffix', 'domain_keyword', 'ip_cidr', 'process_name')
_MIN_CLASSICAL_RULE_PARTS = 2


class SingBoxRenderError(ValueError):
    """Raised when a native sing-box template cannot be rendered safely."""


class SingBoxBinaryUnavailableError(RuntimeError):
    """Raised when the configured sing-box validator is missing or untrusted."""


class SingBoxConfigValidationError(ValueError):
    """Raised when sing-box rejects a rendered configuration."""


def _raise_binary_unavailable(message: str) -> NoReturn:
    raise SingBoxBinaryUnavailableError(message)


def _raise_config_validation_error(message: str) -> NoReturn:
    raise SingBoxConfigValidationError(message)


def _raise_render_error(message: str, cause: Exception | None = None) -> NoReturn:
    if cause is None:
        raise SingBoxRenderError(message)
    raise SingBoxRenderError(message) from cause


@dataclass(frozen=True, slots=True)
class RuleSetSourceSpec:
    source: str
    tag: str
    behavior: Literal['classical', 'domain', 'ipcidr']


@dataclass(frozen=True, slots=True)
class RuleSetArtifact:
    digest: str
    content: bytes


@dataclass(frozen=True, slots=True)
class SingBoxRenderResult:
    content: bytes
    rule_sets: tuple[RuleSetArtifact, ...]
    warnings: tuple[str, ...]
    dropped_nodes: tuple[str, ...] = ()


class SingBox113Renderer:
    """Render a complete native sing-box 1.13 template from canonical nodes and rule sources."""

    def required_rule_sources(self, template_content: str) -> tuple[RuleSetSourceSpec, ...]:
        document = self._load_template(template_content)
        return self._find_rule_set_marker(document)[1]

    def render(
        self,
        template_content: str,
        nodes: Sequence[ProxyNodeModel],
        rule_source_contents: Mapping[str, str],
        rule_set_url: Callable[[str], str],
        *,
        dropped_nodes: Sequence[str] = (),
    ) -> SingBoxRenderResult:
        document = self._load_template(template_content)
        node_outbounds, warnings = self._convert_nodes(nodes)
        node_tags = [str(outbound['tag']) for outbound in node_outbounds]
        self._expand_node_outbounds(document, node_outbounds)
        self._expand_node_tags(document, node_tags)

        rule_set_path, source_specs = self._find_rule_set_marker(document)
        rule_set_definitions: list[dict[str, object]] = []
        artifacts_by_digest: dict[str, RuleSetArtifact] = {}
        for spec in source_specs:
            content = rule_source_contents.get(spec.source)
            if content is None:
                _raise_render_error(f'rule source not found: {spec.source}')
            artifact = self._compile_rule_set(content, spec.behavior)
            artifacts_by_digest.setdefault(artifact.digest, artifact)
            rule_set_definitions.append(
                {
                    'type': 'remote',
                    'tag': spec.tag,
                    'format': 'source',
                    'url': rule_set_url(artifact.digest),
                }
            )
        self._replace_list_marker(document, rule_set_path, 'rule_sets', rule_set_definitions)
        self._reject_residual_markers(document)
        self._validate_references(document)
        rendered = self._canonical_json(document)
        return SingBoxRenderResult(
            content=rendered,
            rule_sets=tuple(artifacts_by_digest.values()),
            warnings=tuple(warnings),
            dropped_nodes=tuple(dropped_nodes),
        )

    @staticmethod
    def _load_template(template_content: str) -> dict[str, object]:
        try:
            document = json.loads(template_content)
        except json.JSONDecodeError as exc:
            _raise_render_error(f'sing-box template must be valid JSON: {exc.msg}', exc)
        if not isinstance(document, dict):
            _raise_render_error('sing-box template must decode to an object')
        SingBox113Renderer._reject_string_interpolation(document)
        return deepcopy(document)

    @staticmethod
    def _reject_string_interpolation(value: object, path: str = '$') -> None:
        if isinstance(value, str):
            if '$csm' in value:
                _raise_render_error(f'string interpolation is not allowed at {path}')
            return
        if isinstance(value, list):
            for index, item in enumerate(value):
                SingBox113Renderer._reject_string_interpolation(item, f'{path}[{index}]')
            return
        if isinstance(value, dict):
            for key, item in value.items():
                SingBox113Renderer._reject_string_interpolation(item, f'{path}.{key}')

    @staticmethod
    def _is_marker(value: object, marker: str) -> bool:
        return isinstance(value, dict) and value.get('$csm') == marker

    @classmethod
    def _expand_node_outbounds(cls, document: dict[str, object], node_outbounds: list[dict[str, object]]) -> None:
        outbounds = document.get('outbounds')
        if not isinstance(outbounds, list):
            _raise_render_error('sing-box template outbounds must be an array')
        marker_indexes = [index for index, value in enumerate(outbounds) if cls._is_marker(value, 'node_outbounds')]
        if len(marker_indexes) != 1:
            _raise_render_error('sing-box template requires exactly one node_outbounds marker in outbounds')
        marker = outbounds[marker_indexes[0]]
        if marker != {'$csm': 'node_outbounds'}:
            _raise_render_error('node_outbounds marker has unsupported fields')
        index = marker_indexes[0]
        outbounds[index : index + 1] = node_outbounds

    @classmethod
    def _expand_node_tags(cls, document: dict[str, object], node_tags: list[str]) -> None:
        outbounds = document.get('outbounds')
        if not isinstance(outbounds, list):
            _raise_render_error('sing-box template outbounds must be an array')
        marker_count = 0
        for outbound in outbounds:
            if not isinstance(outbound, dict):
                _raise_render_error('sing-box template outbounds entries must be objects')
            members = outbound.get('outbounds')
            if not isinstance(members, list):
                continue
            marker_indexes = [index for index, value in enumerate(members) if cls._is_marker(value, 'node_tags')]
            if not marker_indexes:
                continue
            if outbound.get('type') not in {'selector', 'urltest'}:
                _raise_render_error('node_tags marker is only allowed in selector or urltest outbounds')
            for index in reversed(marker_indexes):
                marker = members[index]
                if marker != {'$csm': 'node_tags'}:
                    _raise_render_error('node_tags marker has unsupported fields')
                members[index : index + 1] = node_tags
                marker_count += 1
        if marker_count == 0:
            _raise_render_error('sing-box template requires at least one node_tags marker')

    @classmethod
    def _find_rule_set_marker(
        cls,
        document: dict[str, object],
    ) -> tuple[tuple[str, str, int], tuple[RuleSetSourceSpec, ...]]:
        route = document.get('route')
        if not isinstance(route, dict):
            _raise_render_error('sing-box template route must be an object')
        rule_sets = route.get('rule_set')
        if not isinstance(rule_sets, list):
            _raise_render_error('sing-box template route.rule_set must be an array')
        markers = [(index, value) for index, value in enumerate(rule_sets) if cls._is_marker(value, 'rule_sets')]
        if len(markers) != 1:
            _raise_render_error('sing-box template requires exactly one rule_sets marker in route.rule_set')
        index, marker = markers[0]
        if not isinstance(marker, dict) or set(marker) != {'$csm', 'sources'}:
            _raise_render_error('rule_sets marker must contain only $csm and sources')
        raw_sources = marker.get('sources')
        if not isinstance(raw_sources, list):
            _raise_render_error('rule_sets marker sources must be an array')
        return ('route', 'rule_set', index), cls._parse_rule_set_sources(raw_sources)

    @staticmethod
    def _parse_rule_set_sources(raw_sources: list[object]) -> tuple[RuleSetSourceSpec, ...]:
        specs: list[RuleSetSourceSpec] = []
        seen_tags: set[str] = set()
        for source_index, raw_source in enumerate(raw_sources):
            spec = SingBox113Renderer._parse_rule_set_source(source_index, raw_source)
            if spec.tag in seen_tags:
                _raise_render_error(f'duplicate rule-set tag: {spec.tag}')
            seen_tags.add(spec.tag)
            specs.append(spec)
        return tuple(specs)

    @staticmethod
    def _parse_rule_set_source(source_index: int, raw_source: object) -> RuleSetSourceSpec:
        if not isinstance(raw_source, dict) or set(raw_source) != {'source', 'tag', 'behavior'}:
            _raise_render_error(f'rule_sets source {source_index} has unsupported fields')
        source = raw_source.get('source')
        tag = raw_source.get('tag')
        behavior = raw_source.get('behavior')
        if not isinstance(source, str) or not source.strip():
            _raise_render_error(f'rule_sets source {source_index} requires a non-empty source')
        if not isinstance(tag, str) or not tag.strip():
            _raise_render_error(f'rule_sets source {source_index} requires a non-empty tag')
        if not isinstance(behavior, str) or behavior not in _RULE_BEHAVIORS:
            _raise_render_error(f'rule_sets source {source_index} uses unsupported behavior: {behavior!r}')
        normalized_behavior = cast("Literal['classical', 'domain', 'ipcidr']", behavior)
        return RuleSetSourceSpec(source.strip(), tag.strip(), normalized_behavior)

    @staticmethod
    def _replace_list_marker(
        document: dict[str, object],
        path: tuple[str, str, int],
        marker: str,
        replacements: list[dict[str, object]],
    ) -> None:
        route = document.get(path[0])
        if not isinstance(route, dict):
            _raise_render_error('sing-box template route must be an object')
        values = route.get(path[1])
        if not isinstance(values, list):
            _raise_render_error('sing-box template route.rule_set must be an array')
        index = path[2]
        if not SingBox113Renderer._is_marker(values[index], marker):
            _raise_render_error(f'{marker} marker moved during rendering')
        values[index : index + 1] = replacements

    @staticmethod
    def _convert_nodes(nodes: Sequence[ProxyNodeModel]) -> tuple[list[dict[str, object]], list[str]]:
        outbounds: list[dict[str, object]] = []
        warnings: list[str] = []
        seen_tags: set[str] = set()
        for node in nodes:
            if node.name in seen_tags:
                _raise_render_error(f'duplicate outbound tag: {node.name}')
            seen_tags.add(node.name)
            if isinstance(node, ShadowsocksNode):
                outbound = SingBox113Renderer._convert_shadowsocks(node)
            elif isinstance(node, TrojanNode):
                outbound, warning = SingBox113Renderer._convert_trojan(node)
                if warning is not None:
                    warnings.append(warning)
            elif isinstance(node, AnyTLSNode):
                outbound, warning = SingBox113Renderer._convert_anytls(node)
                if warning is not None:
                    warnings.append(warning)
            else:
                _raise_render_error(f'unsupported sing-box proxy node type: {node.type}')
            outbounds.append(outbound)
        if not outbounds:
            _raise_render_error('at least one proxy node is required')
        return outbounds, warnings

    @staticmethod
    def _convert_shadowsocks(node: ShadowsocksNode) -> dict[str, object]:
        outbound: dict[str, object] = {
            'type': 'shadowsocks',
            'tag': node.name,
            'server': node.server,
            'server_port': node.port,
            'method': node.cipher,
            'password': node.password,
        }
        if not node.udp:
            outbound['network'] = 'tcp'
        if node.plugin is None:
            if node.plugin_opts:
                _raise_render_error(f'shadowsocks node {node.name!r} has plugin options without a plugin')
            return outbound
        if node.plugin != 'obfs':
            _raise_render_error(f'unsupported shadowsocks plugin for {node.name!r}: {node.plugin}')
        options = node.plugin_opts or {}
        unsupported_options = set(options) - {'host', 'mode'}
        if unsupported_options:
            names = ', '.join(sorted(unsupported_options))
            _raise_render_error(f'unsupported obfs options for {node.name!r}: {names}')
        mode = options.get('mode')
        if mode not in {'http', 'tls'}:
            _raise_render_error(f'obfs mode for {node.name!r} must be http or tls')
        plugin_options = f'obfs={mode}'
        host = options.get('host')
        if host:
            plugin_options += f';obfs-host={host}'
        outbound['plugin'] = 'obfs-local'
        outbound['plugin_opts'] = plugin_options
        return outbound

    @staticmethod
    def _convert_trojan(node: TrojanNode) -> tuple[dict[str, object], str | None]:
        if node.network != 'tcp':
            _raise_render_error(f'unsupported trojan transport for {node.name!r}: {node.network}')
        tls: dict[str, object] = {'enabled': True}
        if node.sni is not None:
            tls['server_name'] = node.sni
        warning = None
        if node.skip_cert_verify:
            tls['insecure'] = True
            warning = f'trojan node {node.name!r} enables tls.insecure'
        outbound: dict[str, object] = {
            'type': 'trojan',
            'tag': node.name,
            'server': node.server,
            'server_port': node.port,
            'password': node.password,
            'tls': tls,
        }
        if not node.udp:
            outbound['network'] = 'tcp'
        return outbound, warning

    @staticmethod
    def _convert_anytls(node: AnyTLSNode) -> tuple[dict[str, object], str | None]:
        tls: dict[str, object] = {'enabled': True}
        if node.sni is not None:
            tls['server_name'] = node.sni
        if node.alpn is not None:
            tls['alpn'] = node.alpn
        if node.client_fingerprint is not None:
            tls['utls'] = {'enabled': True, 'fingerprint': node.client_fingerprint}
        warning = None
        if node.skip_cert_verify:
            tls['insecure'] = True
            warning = f'anytls node {node.name!r} enables tls.insecure'
        outbound: dict[str, object] = {
            'type': 'anytls',
            'tag': node.name,
            'server': node.server,
            'server_port': node.port,
            'password': node.password,
            'tls': tls,
        }
        if not node.udp:
            outbound['network'] = 'tcp'
        if node.idle_session_check_interval is not None:
            outbound['idle_session_check_interval'] = f'{node.idle_session_check_interval}s'
        if node.idle_session_timeout is not None:
            outbound['idle_session_timeout'] = f'{node.idle_session_timeout}s'
        if node.min_idle_session is not None:
            outbound['min_idle_session'] = node.min_idle_session
        if node.tfo:
            outbound['tcp_fast_open'] = True
        return outbound, warning

    @staticmethod
    def _compile_rule_set(content: str, behavior: str) -> RuleSetArtifact:
        try:
            document = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            _raise_render_error('rule source must be valid YAML', exc)
        entries = document.get('payload') if isinstance(document, dict) else document
        if not isinstance(entries, list) or any(not isinstance(entry, str) for entry in entries):
            _raise_render_error('rule source must contain a string payload array')

        values: dict[str, set[str]] = {field: set() for field in _RULE_FIELDS}
        for raw_entry in entries:
            entry = raw_entry.strip()
            if not entry or entry.startswith('#'):
                continue
            if behavior == 'domain':
                SingBox113Renderer._compile_domain_entry(entry, values)
            elif behavior == 'ipcidr':
                values['ip_cidr'].add(SingBox113Renderer._canonical_network(entry))
            elif behavior == 'classical':
                SingBox113Renderer._compile_classical_entry(entry, values)
            else:
                _raise_render_error(f'unsupported rule-set behavior: {behavior}')
        rules = [{field: sorted(values[field])} for field in _RULE_FIELDS if values[field]]
        if not rules:
            _raise_render_error('rule source produced no supported rules')
        rendered = SingBox113Renderer._canonical_json({'version': RULE_SET_VERSION, 'rules': rules})
        return RuleSetArtifact(hashlib.sha256(rendered).hexdigest(), rendered)

    @staticmethod
    def _compile_domain_entry(entry: str, values: dict[str, set[str]]) -> None:
        if entry.startswith(('+.', '.')):
            domain = entry[2:] if entry.startswith('+.') else entry[1:]
            if not domain or '*' in domain:
                _raise_render_error(f'unsupported domain rule: {entry}')
            values['domain_suffix'].add(domain)
            return
        if '*' in entry:
            _raise_render_error(f'unsupported domain rule: {entry}')
        values['domain'].add(entry)

    @staticmethod
    def _compile_classical_entry(entry: str, values: dict[str, set[str]]) -> None:
        parts = next(csv.reader([entry], skipinitialspace=True))
        if len(parts) < _MIN_CLASSICAL_RULE_PARTS:
            _raise_render_error(f'invalid classical rule: {entry}')
        rule_type = parts[0].strip().upper()
        value = parts[1].strip()
        options = [option.strip().lower() for option in parts[2:] if option.strip()]
        if rule_type in {'IP-CIDR', 'IP-CIDR6'}:
            if any(option != 'no-resolve' for option in options):
                _raise_render_error(f'unsupported classical rule options: {entry}')
            values['ip_cidr'].add(SingBox113Renderer._canonical_network(value))
            return
        if options:
            _raise_render_error(f'unsupported classical rule options: {entry}')
        field_by_type = {
            'DOMAIN': 'domain',
            'DOMAIN-SUFFIX': 'domain_suffix',
            'DOMAIN-KEYWORD': 'domain_keyword',
            'PROCESS-NAME': 'process_name',
        }
        field = field_by_type.get(rule_type)
        if field is None or not value:
            _raise_render_error(f'unsupported classical rule: {entry}')
        values[field].add(value)

    @staticmethod
    def _canonical_network(value: str) -> str:
        try:
            return str(ipaddress.ip_network(value, strict=False))
        except ValueError as exc:
            _raise_render_error(f'invalid IP CIDR rule: {value}', exc)

    @staticmethod
    def _reject_residual_markers(value: object, path: str = '$') -> None:
        if isinstance(value, list):
            for index, item in enumerate(value):
                SingBox113Renderer._reject_residual_markers(item, f'{path}[{index}]')
            return
        if isinstance(value, dict):
            if '$csm' in value:
                _raise_render_error(f'unsupported or misplaced $csm marker at {path}')
            for key, item in value.items():
                SingBox113Renderer._reject_residual_markers(item, f'{path}.{key}')

    @staticmethod
    def _validate_references(document: dict[str, object]) -> None:
        outbounds, outbound_tags = SingBox113Renderer._collect_outbounds(document)
        endpoint_tags = SingBox113Renderer._collect_endpoint_tags(document, outbound_tags)
        SingBox113Renderer._validate_outbound_members(outbounds, outbound_tags)
        route = document.get('route')
        if not isinstance(route, dict):
            _raise_render_error('sing-box route must be an object')
        rule_set_tags = SingBox113Renderer._collect_rule_set_tags(route)
        SingBox113Renderer._validate_route_references(route, outbound_tags | endpoint_tags, rule_set_tags)

    @staticmethod
    def _collect_outbounds(document: dict[str, object]) -> tuple[list[dict[str, object]], set[str]]:
        raw_outbounds = document.get('outbounds')
        if not isinstance(raw_outbounds, list):
            _raise_render_error('sing-box outbounds must be an array')
        outbounds: list[dict[str, object]] = []
        tags: set[str] = set()
        for index, outbound in enumerate(raw_outbounds):
            if not isinstance(outbound, dict):
                _raise_render_error(f'outbound {index} must be an object')
            tag = outbound.get('tag')
            if not isinstance(tag, str) or not tag:
                _raise_render_error(f'outbound {index} requires a non-empty tag')
            if tag in tags:
                _raise_render_error(f'duplicate outbound tag: {tag}')
            tags.add(tag)
            outbounds.append(outbound)
        return outbounds, tags

    @staticmethod
    def _collect_endpoint_tags(document: dict[str, object], outbound_tags: set[str]) -> set[str]:
        raw_endpoints = document.get('endpoints', [])
        if not isinstance(raw_endpoints, list):
            _raise_render_error('sing-box endpoints must be an array')
        endpoint_tags: set[str] = set()
        for endpoint in raw_endpoints:
            if not isinstance(endpoint, dict) or not isinstance(endpoint.get('tag'), str):
                _raise_render_error('each sing-box endpoint requires a tag')
            tag = str(endpoint['tag'])
            if tag in outbound_tags or tag in endpoint_tags:
                _raise_render_error(f'duplicate route tag: {tag}')
            endpoint_tags.add(tag)
        return endpoint_tags

    @staticmethod
    def _validate_outbound_members(outbounds: list[dict[str, object]], outbound_tags: set[str]) -> None:
        for outbound in outbounds:
            members = outbound.get('outbounds')
            if not isinstance(members, list):
                continue
            unknown = [member for member in members if not isinstance(member, str) or member not in outbound_tags]
            if unknown:
                _raise_render_error(f'outbound {outbound["tag"]!r} references unknown tags: {unknown!r}')

    @staticmethod
    def _collect_rule_set_tags(route: dict[str, object]) -> set[str]:
        rule_sets = route.get('rule_set', [])
        if not isinstance(rule_sets, list):
            _raise_render_error('sing-box route.rule_set must be an array')
        tags: set[str] = set()
        for rule_set in rule_sets:
            if not isinstance(rule_set, dict) or not isinstance(rule_set.get('tag'), str):
                _raise_render_error('each sing-box rule-set requires a tag')
            tag = str(rule_set['tag'])
            if tag in tags:
                _raise_render_error(f'duplicate rule-set tag: {tag}')
            tags.add(tag)
        return tags

    @staticmethod
    def _validate_route_references(
        route: dict[str, object],
        route_tags: set[str],
        rule_set_tags: set[str],
    ) -> None:
        final = route.get('final')
        if final is not None and (not isinstance(final, str) or final not in route_tags):
            _raise_render_error(f'route.final references unknown tag: {final!r}')
        rules = route.get('rules', [])
        if not isinstance(rules, list):
            _raise_render_error('sing-box route.rules must be an array')
        for index, rule in enumerate(rules):
            SingBox113Renderer._validate_route_rule(index, rule, route_tags, rule_set_tags)

    @staticmethod
    def _validate_route_rule(
        index: int,
        rule: object,
        route_tags: set[str],
        rule_set_tags: set[str],
    ) -> None:
        if not isinstance(rule, dict):
            _raise_render_error(f'route rule {index} must be an object')
        outbound = rule.get('outbound')
        if outbound is not None and (not isinstance(outbound, str) or outbound not in route_tags):
            _raise_render_error(f'route rule {index} references unknown outbound: {outbound!r}')
        referenced_rule_sets = rule.get('rule_set')
        if referenced_rule_sets is None:
            return
        if not isinstance(referenced_rule_sets, list) or any(
            not isinstance(tag, str) or tag not in rule_set_tags for tag in referenced_rule_sets
        ):
            _raise_render_error(f'route rule {index} references unknown rule-set tags')

    @staticmethod
    def _canonical_json(document: object) -> bytes:
        return (json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()


class SingBoxArtifactStore:
    """Publish immutable rule sets and the latest validated profile snapshot atomically."""

    def __init__(self, root: Path):
        self.root = root

    def publish_rule_set(self, artifact: RuleSetArtifact) -> Path:
        expected_digest = hashlib.sha256(artifact.content).hexdigest()
        if expected_digest != artifact.digest:
            message = 'rule-set content does not match its digest'
            raise ValueError(message)
        path = self.rule_set_path(artifact.digest)
        if path.exists():
            if path.read_bytes() != artifact.content:
                message = f'rule-set digest collision: {artifact.digest}'
                raise ValueError(message)
            return path
        self._atomic_write(path, artifact.content)
        return path

    def publish_config(self, public_id: str, content: bytes) -> Path:
        path = self.root / 'configs' / public_id / 'current.json'
        self._atomic_write(path, content)
        return path

    def rule_set_path(self, digest: str) -> Path:
        return self.root / 'rule-sets' / f'v{RULE_SET_VERSION}' / f'{digest}.json'

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        file_descriptor, temporary_name = tempfile.mkstemp(prefix=f'.{path.name}.', dir=path.parent)
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(file_descriptor, 'wb') as temporary_file:
                temporary_file.write(content)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            temporary_path.replace(path)
        finally:
            temporary_path.unlink(missing_ok=True)


class SingBoxValidator:
    """Verify a pinned sing-box binary and validate every published configuration."""

    def __init__(self, binary: Path, expected_sha256: str):
        self.binary = binary
        self.expected_sha256 = expected_sha256.lower()
        self._verified = False
        self._lock = threading.Lock()

    def _run(self, arguments: list[str]) -> subprocess.CompletedProcess[str]:
        command = [str(self.binary), *arguments]
        return subprocess.run(  # noqa: S603 - the executable is verified by path, version, and SHA-256.
            command,
            check=False,
            capture_output=True,
            text=True,
        )

    def check(self, content: bytes, temporary_directory: Path) -> None:
        self._verify_binary()
        temporary_directory.mkdir(parents=True, exist_ok=True)
        file_descriptor, temporary_name = tempfile.mkstemp(suffix='.json', dir=temporary_directory)
        config_path = Path(temporary_name)
        try:
            with os.fdopen(file_descriptor, 'wb') as config_file:
                config_file.write(content)
                config_file.flush()
                os.fsync(config_file.fileno())
            result = self._run(['check', '-c', str(config_path)])
            if result.returncode != 0:
                diagnostic = (result.stderr or result.stdout).strip() or f'exit code {result.returncode}'
                _raise_config_validation_error(f'sing-box check failed: {diagnostic}')
        finally:
            config_path.unlink(missing_ok=True)

    def check_rule_set(self, content: bytes, temporary_directory: Path) -> None:
        self._verify_binary()
        temporary_directory.mkdir(parents=True, exist_ok=True)
        source_descriptor, source_name = tempfile.mkstemp(suffix='.json', dir=temporary_directory)
        source_path = Path(source_name)
        output_path = source_path.with_suffix('.srs')
        try:
            with os.fdopen(source_descriptor, 'wb') as source_file:
                source_file.write(content)
                source_file.flush()
                os.fsync(source_file.fileno())
            result = self._run(
                [
                    'rule-set',
                    'compile',
                    '--output',
                    str(output_path),
                    str(source_path),
                ]
            )
            if result.returncode != 0:
                diagnostic = (result.stderr or result.stdout).strip() or f'exit code {result.returncode}'
                _raise_config_validation_error(f'sing-box rule-set compile failed: {diagnostic}')
        finally:
            source_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)

    def _verify_binary(self) -> None:
        with self._lock:
            if self._verified:
                return
            if not self.binary.is_file():
                _raise_binary_unavailable(f'sing-box binary not found: {self.binary}')
            digest = hashlib.sha256(self.binary.read_bytes()).hexdigest()
            if digest != self.expected_sha256:
                _raise_binary_unavailable('sing-box binary SHA-256 does not match configured digest')
            result = self._run(['version'])
            version_output = f'{result.stdout}\n{result.stderr}'
            if result.returncode != 0 or SING_BOX_COMPATIBILITY_VERSION not in version_output:
                _raise_binary_unavailable(f'sing-box binary version must contain {SING_BOX_COMPATIBILITY_VERSION}')
            self._verified = True


__all__ = [
    'RULE_SET_VERSION',
    'SING_BOX_COMPATIBILITY_VERSION',
    'SING_BOX_SCHEMA_VERSION',
    'RuleSetArtifact',
    'RuleSetSourceSpec',
    'SingBox113Renderer',
    'SingBoxArtifactStore',
    'SingBoxBinaryUnavailableError',
    'SingBoxConfigValidationError',
    'SingBoxRenderError',
    'SingBoxRenderResult',
    'SingBoxValidator',
]
