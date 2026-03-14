"""Pydantic schemas for template patches and composite templates."""

from __future__ import annotations

import datetime as dt  # noqa: TC003
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .schemas import ORMReadModel, TemplateSummaryRead, _normalize_name

PatchOperationType = Literal[
    'delete',
    'list_append',
    'list_insert',
    'list_remove',
    'list_replace',
    'merge',
    'set',
]


class PatchOperation(BaseModel):
    op: PatchOperationType
    path: str = Field(min_length=1)
    value: object | None = None
    index: int | None = Field(default=None, ge=0)
    old_value: object | None = None

    @field_validator('path')
    @classmethod
    def validate_path(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = 'path must not be blank'
            raise ValueError(msg)
        return normalized

    @model_validator(mode='after')
    def validate_fields(self) -> PatchOperation:
        requires_value = {'list_append', 'list_insert', 'list_remove', 'list_replace', 'merge', 'set'}
        requires_index = {'list_insert', 'list_replace'}

        if self.op in requires_value and 'value' not in self.model_fields_set:
            msg = f'value is required for {self.op}'
            raise ValueError(msg)
        if self.op not in requires_value and 'value' in self.model_fields_set:
            msg = f'value is not supported for {self.op}'
            raise ValueError(msg)
        if self.op in requires_index and self.index is None:
            msg = f'index is required for {self.op}'
            raise ValueError(msg)
        if self.op not in requires_index and self.index is not None:
            msg = f'index is not supported for {self.op}'
            raise ValueError(msg)
        if self.op != 'list_replace' and 'old_value' in self.model_fields_set:
            msg = 'old_value is only supported for list_replace'
            raise ValueError(msg)
        return self


class TemplatePatchSummaryRead(ORMReadModel):
    id: int
    name: str
    description: str | None


class TemplatePatchRead(ORMReadModel):
    id: int
    name: str
    description: str | None
    operations: list[PatchOperation]
    created_at: dt.datetime
    updated_at: dt.datetime


class TemplatePatchCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    operations: list[PatchOperation] = Field(default_factory=list)

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        return str(_normalize_name(value, required=True))


class TemplatePatchUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    operations: list[PatchOperation] | None = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        return _normalize_name(value, required=False)


class TemplatePatchPreviewRequest(BaseModel):
    base_template_id: int = Field(ge=1)


class CompositeTemplateRead(ORMReadModel):
    id: int
    name: str
    base_template_id: int
    patch_sequence: list[int]
    cached_content: str
    created_at: dt.datetime
    updated_at: dt.datetime
    base_template: TemplateSummaryRead
    patches: list[TemplatePatchSummaryRead]


class CompositeTemplateCreate(BaseModel):
    name: str = Field(min_length=1)
    base_template_id: int = Field(ge=1)
    patch_sequence: list[int] = Field(default_factory=list)

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        return str(_normalize_name(value, required=True))

    @field_validator('patch_sequence')
    @classmethod
    def validate_patch_sequence(cls, value: list[int]) -> list[int]:
        if any(patch_id < 1 for patch_id in value):
            msg = 'patch_sequence entries must be positive integers'
            raise ValueError(msg)
        return value


class CompositeTemplateUpdate(BaseModel):
    name: str | None = None
    base_template_id: int | None = Field(default=None, ge=1)
    patch_sequence: list[int] | None = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        return _normalize_name(value, required=False)

    @field_validator('patch_sequence')
    @classmethod
    def validate_patch_sequence(cls, value: list[int] | None) -> list[int] | None:
        if value is not None and any(patch_id < 1 for patch_id in value):
            msg = 'patch_sequence entries must be positive integers'
            raise ValueError(msg)
        return value


class CompositeTemplatePreviewRequest(BaseModel):
    base_template_id: int = Field(ge=1)
    patch_sequence: list[int] = Field(default_factory=list)

    @field_validator('patch_sequence')
    @classmethod
    def validate_patch_sequence(cls, value: list[int]) -> list[int]:
        if any(patch_id < 1 for patch_id in value):
            msg = 'patch_sequence entries must be positive integers'
            raise ValueError(msg)
        return value


class CompositePreviewRead(BaseModel):
    content: dict[str, object]


__all__ = [
    'CompositePreviewRead',
    'CompositeTemplateCreate',
    'CompositeTemplatePreviewRequest',
    'CompositeTemplateRead',
    'CompositeTemplateUpdate',
    'PatchOperation',
    'PatchOperationType',
    'TemplatePatchCreate',
    'TemplatePatchPreviewRequest',
    'TemplatePatchRead',
    'TemplatePatchSummaryRead',
    'TemplatePatchUpdate',
]
