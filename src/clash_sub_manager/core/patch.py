"""Deterministic template patch application."""

from __future__ import annotations

from copy import deepcopy
from typing import Final

_PATCH_OPS: Final[frozenset[str]] = frozenset(
    {
        'delete',
        'list_append',
        'list_insert',
        'list_remove',
        'list_replace',
        'merge',
        'set',
    }
)
_MISSING_VALUE: Final[object] = object()


class PatchValidationError(ValueError):
    """Raised when a patch operation cannot be applied safely."""


class PatchEngine:
    """Apply ordered, atomic patch operations to a template mapping."""

    def apply(self, template: dict[str, object], operations: list[dict[str, object]]) -> dict[str, object]:
        if not isinstance(template, dict):
            msg = 'template must be a mapping'
            raise TypeError(msg)

        updated = deepcopy(template)
        for index, operation in enumerate(operations):
            self._apply_operation(updated, operation, operation_index=index)
        return updated

    def _apply_operation(
        self,
        template: dict[str, object],
        operation: dict[str, object],
        *,
        operation_index: int,
    ) -> None:
        op = self._require_op(operation, operation_index=operation_index)
        path = self._require_path(operation, operation_index=operation_index)
        tokens = self._parse_path(path, operation_index=operation_index)
        parent, key = self._resolve_parent(template, tokens, operation_index=operation_index)

        if op in {'set', 'delete'}:
            self._apply_scalar_operation(parent, key, operation, operation_index=operation_index)
            return
        if op == 'merge':
            self._apply_merge(parent, key, operation, operation_index=operation_index)
            return
        self._apply_list_operation(parent, key, path, operation, operation_index=operation_index)

    @staticmethod
    def _require_op(operation: dict[str, object], *, operation_index: int) -> str:
        op = operation.get('op')
        if not isinstance(op, str) or op not in _PATCH_OPS:
            msg = f'operation {operation_index} uses unsupported op: {op!r}'
            raise PatchValidationError(msg)
        return op

    @staticmethod
    def _require_path(operation: dict[str, object], *, operation_index: int) -> str:
        path = operation.get('path')
        if not isinstance(path, str) or not path.strip():
            msg = f'operation {operation_index} must include a non-empty path'
            raise PatchValidationError(msg)
        return path

    def _apply_scalar_operation(
        self,
        parent: dict[str, object] | list[object],
        key: str,
        operation: dict[str, object],
        *,
        operation_index: int,
    ) -> None:
        op = str(operation['op'])
        if op == 'delete':
            self._delete_value(parent, key, operation_index=operation_index)
            return
        self._set_value(
            parent,
            key,
            self._require_value(operation, operation_index=operation_index),
            operation_index=operation_index,
        )

    def _apply_merge(
        self,
        parent: dict[str, object] | list[object],
        key: str,
        operation: dict[str, object],
        *,
        operation_index: int,
    ) -> None:
        value = operation.get('value')
        if not isinstance(value, dict):
            msg = f'operation {operation_index} merge value must be a mapping'
            raise PatchValidationError(msg)

        target = self._get_value(parent, key, operation_index=operation_index)
        if not isinstance(target, dict):
            msg = f'operation {operation_index} merge target must be a mapping'
            raise PatchValidationError(msg)
        self._deep_merge(target, value)

    def _apply_list_operation(
        self,
        parent: dict[str, object] | list[object],
        key: str,
        path: str,
        operation: dict[str, object],
        *,
        operation_index: int,
    ) -> None:
        op = str(operation['op'])
        target = self._get_value(parent, key, operation_index=operation_index)
        if not isinstance(target, list):
            msg = f'operation {operation_index} target must be a list'
            raise PatchValidationError(msg)

        if op == 'list_append':
            target.append(self._require_value(operation, operation_index=operation_index))
            return
        if op == 'list_insert':
            index = self._require_list_index(operation.get('index'), target, operation_index=operation_index, allow_end=True)
            target.insert(index, self._require_value(operation, operation_index=operation_index))
            return
        if op == 'list_remove':
            self._remove_from_list(target, path, operation, operation_index=operation_index)
            return
        self._replace_list_item(target, path, operation, operation_index=operation_index)

    def _remove_from_list(
        self,
        target: list[object],
        path: str,
        operation: dict[str, object],
        *,
        operation_index: int,
    ) -> None:
        index = self._require_list_index(operation.get('index'), target, operation_index=operation_index, allow_end=False)
        old_value = operation.get('old_value', _MISSING_VALUE)
        if old_value is not _MISSING_VALUE and target[index] != old_value:
            msg = f'operation {operation_index} old_value mismatch at path {path!r}'
            raise PatchValidationError(msg)
        del target[index]

    def _replace_list_item(
        self,
        target: list[object],
        path: str,
        operation: dict[str, object],
        *,
        operation_index: int,
    ) -> None:
        index = self._require_list_index(operation.get('index'), target, operation_index=operation_index, allow_end=False)
        old_value = operation.get('old_value', _MISSING_VALUE)
        if old_value is not _MISSING_VALUE and target[index] != old_value:
            msg = f'operation {operation_index} old_value mismatch at path {path!r}'
            raise PatchValidationError(msg)
        target[index] = self._require_value(operation, operation_index=operation_index)

    @staticmethod
    def _require_value(operation: dict[str, object], *, operation_index: int) -> object:
        if 'value' not in operation:
            msg = f'operation {operation_index} requires value'
            raise PatchValidationError(msg)
        return deepcopy(operation['value'])

    @staticmethod
    def _parse_path(path: str, *, operation_index: int) -> list[str]:
        tokens = [token.strip() for token in path.split('.')]
        if any(token == '' for token in tokens):
            msg = f'operation {operation_index} path must not contain empty segments'
            raise PatchValidationError(msg)
        return tokens

    def _resolve_parent(
        self,
        template: dict[str, object],
        tokens: list[str],
        *,
        operation_index: int,
    ) -> tuple[dict[str, object] | list[object], str]:
        current: dict[str, object] | list[object] = template
        for token in tokens[:-1]:
            current = self._descend_container(current, token, operation_index=operation_index)
        return current, tokens[-1]

    def _descend_container(
        self,
        current: dict[str, object] | list[object],
        token: str,
        *,
        operation_index: int,
    ) -> dict[str, object] | list[object]:
        child = self._lookup(current, token, operation_index=operation_index)
        if not isinstance(child, (dict, list)):
            msg = f'operation {operation_index} path segment {token!r} does not resolve to a container'
            raise PatchValidationError(msg)
        return child

    def _get_value(
        self,
        parent: dict[str, object] | list[object],
        key: str,
        *,
        operation_index: int,
    ) -> object:
        return self._lookup(parent, key, operation_index=operation_index)

    def _set_value(
        self,
        parent: dict[str, object] | list[object],
        key: str,
        value: object,
        *,
        operation_index: int,
    ) -> None:
        if isinstance(parent, dict):
            if key not in parent:
                msg = f'operation {operation_index} path segment {key!r} does not exist'
                raise PatchValidationError(msg)
            parent[key] = value
            return

        index = self._parse_list_index(key, operation_index=operation_index)
        if index >= len(parent):
            msg = f'operation {operation_index} list index {index} out of range'
            raise PatchValidationError(msg)
        parent[index] = value

    def _delete_value(
        self,
        parent: dict[str, object] | list[object],
        key: str,
        *,
        operation_index: int,
    ) -> None:
        if isinstance(parent, dict):
            if key not in parent:
                msg = f'operation {operation_index} path segment {key!r} does not exist'
                raise PatchValidationError(msg)
            del parent[key]
            return

        index = self._parse_list_index(key, operation_index=operation_index)
        if index >= len(parent):
            msg = f'operation {operation_index} list index {index} out of range'
            raise PatchValidationError(msg)
        del parent[index]

    def _lookup(
        self,
        current: dict[str, object] | list[object],
        token: str,
        *,
        operation_index: int,
    ) -> object:
        if isinstance(current, dict):
            if token not in current:
                msg = f'operation {operation_index} path segment {token!r} does not exist'
                raise PatchValidationError(msg)
            return current[token]

        index = self._parse_list_index(token, operation_index=operation_index)
        if index >= len(current):
            msg = f'operation {operation_index} list index {index} out of range'
            raise PatchValidationError(msg)
        return current[index]

    @staticmethod
    def _parse_list_index(token: str, *, operation_index: int) -> int:
        if not token.isdigit():
            msg = f'operation {operation_index} list path segment must be a non-negative integer: {token!r}'
            raise PatchValidationError(msg)
        return int(token)

    def _require_list_index(
        self,
        raw_index: object,
        target_list: list[object],
        *,
        operation_index: int,
        allow_end: bool,
    ) -> int:
        if not isinstance(raw_index, int):
            msg = f'operation {operation_index} requires integer index'
            raise PatchValidationError(msg)
        upper_bound = len(target_list) if allow_end else len(target_list) - 1
        if raw_index < 0 or raw_index > upper_bound:
            msg = f'operation {operation_index} index {raw_index} out of range'
            raise PatchValidationError(msg)
        return raw_index

    def _deep_merge(self, target: dict[str, object], patch: dict[str, object]) -> None:
        for key, value in patch.items():
            current = target.get(key)
            if isinstance(current, dict) and isinstance(value, dict):
                self._deep_merge(current, value)
                continue
            target[key] = deepcopy(value)


__all__ = ['PatchEngine', 'PatchValidationError']
