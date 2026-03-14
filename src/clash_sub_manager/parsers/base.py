"""Shared helpers for protocol-specific parsers."""

from __future__ import annotations

import base64
import binascii
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from urllib.parse import unquote

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping


class ShareLinkParser(ABC):
    """Interface implemented by each share-link parser."""

    scheme: str

    @classmethod
    @abstractmethod
    def parse(cls, url: str) -> object:
        """Parse a share link into a domain model."""


def decode_urlsafe_base64(value: str) -> str:
    """Decode standard or URL-safe base64 content with optional missing padding."""

    normalized = value.strip().replace('-', '+').replace('_', '/')
    padding = '=' * (-len(normalized) % 4)
    try:
        return base64.b64decode(normalized + padding).decode('utf-8')
    except (ValueError, binascii.Error, UnicodeDecodeError) as exc:
        msg = 'invalid base64 payload'
        raise ValueError(msg) from exc


def decode_fragment(value: str) -> str | None:
    decoded = unquote(value).strip()
    return decoded or None


def first_query_value(query: Mapping[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    if not values:
        return None
    value = values[0].strip()
    return value or None


def parse_bool_flag(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {'1', 'true', 'yes', 'on', 'tls'}


def split_subscription_entries(content: str) -> list[str]:
    return [chunk.strip() for chunk in content.replace('\r', '\n').split() if chunk.strip()]


def split_escaped(value: str, separator: str = ';') -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    escaped = False
    for char in value:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == '\\':
            escaped = True
            continue
        if char == separator:
            parts.append(''.join(current))
            current.clear()
            continue
        current.append(char)
    if escaped:
        current.append('\\')
    parts.append(''.join(current))
    return parts


def parse_plugin_payload(payload: str) -> tuple[str, dict[str, str]]:
    segments = [segment for segment in split_escaped(payload) if segment]
    if not segments:
        msg = 'plugin payload must not be empty'
        raise ValueError(msg)
    plugin = segments[0]
    options: dict[str, str] = {}
    for segment in segments[1:]:
        key, separator, raw_value = segment.partition('=')
        options[key if separator else segment] = raw_value if separator else ''
    return plugin, options


def require_keys(mapping: Mapping[str, object], keys: Iterable[str]) -> None:
    missing = [key for key in keys if key not in mapping or mapping[key] in (None, '')]
    if missing:
        msg = f'missing required keys: {", ".join(missing)}'
        raise ValueError(msg)
