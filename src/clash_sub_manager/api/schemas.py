"""Pydantic request and response models for the HTTP API."""

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from ..models import SubscriptionConfig


class ORMReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def _normalize_name(value: str | None, *, required: bool) -> str | None:
    if value is None:
        if required:
            msg = 'name is required'
            raise ValueError(msg)
        return None

    normalized = value.strip()
    if not normalized:
        msg = 'name must not be blank'
        raise ValueError(msg)
    return normalized


def _validate_subscription_ids(value: list[int] | None, *, required: bool) -> list[int] | None:
    if value is None:
        if required:
            msg = 'at least one subscription is required'
            raise ValueError(msg)
        return None

    if not value:
        msg = 'at least one subscription is required'
        raise ValueError(msg)

    if len(set(value)) != len(value):
        msg = 'subscription_ids must be unique'
        raise ValueError(msg)
    return value


def _normalize_excluded_node_names(value: list[str]) -> list[str]:
    normalized = [name.strip() for name in value]
    if any(not name for name in normalized):
        msg = 'excluded node names must not be blank'
        raise ValueError(msg)
    if len(set(normalized)) != len(normalized):
        msg = 'excluded node names must be unique'
        raise ValueError(msg)
    return normalized


class SubscriptionSourceInput(BaseModel):
    url: HttpUrl | None = None
    content: str | None = None
    proxy: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    follow_redirects: bool = True
    timeout_seconds: float = Field(default=5.0, gt=0, allow_inf_nan=False)
    excluded_node_names: list[str] = Field(default_factory=list)

    @field_validator('excluded_node_names')
    @classmethod
    def validate_excluded_node_names(cls, value: list[str]) -> list[str]:
        return _normalize_excluded_node_names(value)

    @model_validator(mode='after')
    def validate_source(self) -> 'SubscriptionSourceInput':
        has_url = self.url is not None
        has_content = self.content is not None and self.content.strip() != ''
        if has_url == has_content:
            msg = 'exactly one of url or content must be provided'
            raise ValueError(msg)
        return self

    def to_subscription_config(self, name: str) -> SubscriptionConfig:
        return SubscriptionConfig(
            name=name,
            url=self.url,
            content=self.content,
            proxy=self.proxy,
            headers=self.headers,
            follow_redirects=self.follow_redirects,
            timeout_seconds=self.timeout_seconds,
            excluded_node_names=self.excluded_node_names,
        )


class ConvertRequest(SubscriptionSourceInput):
    template: dict[str, object] | None = None


class MergeRequest(BaseModel):
    configs: list[SubscriptionSourceInput] = Field(default_factory=list)
    template: dict[str, object] | None = None

    @model_validator(mode='after')
    def validate_configs(self) -> 'MergeRequest':
        if not self.configs:
            msg = 'at least one subscription config is required'
            raise ValueError(msg)
        return self


class SubscriptionSummaryRead(ORMReadModel):
    id: int
    name: str
    enabled: bool


class TemplateSummaryRead(ORMReadModel):
    id: int
    name: str


class SubscriptionRead(ORMReadModel):
    id: int
    name: str
    url: str | None
    content: str | None
    proxy: str | None
    headers: dict[str, str]
    follow_redirects: bool
    timeout_seconds: float
    enabled: bool
    excluded_node_names: list[str]
    last_updated_at: dt.datetime | None


class SubscriptionCreate(SubscriptionSourceInput):
    name: str = Field(min_length=1)
    enabled: bool = True

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        return str(_normalize_name(value, required=True))


class SubscriptionUpdate(BaseModel):
    name: str | None = None
    url: HttpUrl | None = None
    content: str | None = None
    proxy: str | None = None
    headers: dict[str, str] | None = None
    follow_redirects: bool | None = None
    timeout_seconds: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    enabled: bool | None = None
    excluded_node_names: list[str] | None = None

    @field_validator('excluded_node_names')
    @classmethod
    def validate_excluded_node_names(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return _normalize_excluded_node_names(value)

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        return _normalize_name(value, required=False)


def validate_template_metadata(target: str, schema_version: str, template_format: str) -> None:
    if target == 'mihomo' and (schema_version != '1' or template_format != 'yaml'):
        msg = 'mihomo templates require schema_version 1 and format yaml'
        raise ValueError(msg)
    if target == 'sing-box' and (schema_version != '1.13' or template_format != 'json'):
        msg = 'sing-box templates require schema_version 1.13 and format json'
        raise ValueError(msg)


class TemplateRead(ORMReadModel):
    id: int
    name: str
    content: str
    is_default: bool
    target: Literal['mihomo', 'sing-box']
    schema_version: str
    format: Literal['yaml', 'json']


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1)
    content: str
    is_default: bool = False
    target: Literal['mihomo', 'sing-box'] = 'mihomo'
    schema_version: str = '1'
    format: Literal['yaml', 'json'] = 'yaml'

    @model_validator(mode='after')
    def validate_target_metadata(self) -> 'TemplateCreate':
        validate_template_metadata(self.target, self.schema_version, self.format)
        return self

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        return str(_normalize_name(value, required=True))


class TemplateUpdate(BaseModel):
    name: str | None = None
    content: str | None = None
    is_default: bool | None = None
    target: Literal['mihomo', 'sing-box'] | None = None
    schema_version: str | None = None
    format: Literal['yaml', 'json'] | None = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        return _normalize_name(value, required=False)


class RuleSourceRead(ORMReadModel):
    id: int
    name: str
    url: str
    auto_update: bool
    content: str | None
    last_updated_at: dt.datetime | None


class RuleSourceCreate(BaseModel):
    name: str = Field(min_length=1)
    url: HttpUrl
    auto_update: bool = True
    content: str | None = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        return str(_normalize_name(value, required=True))


class RuleSourceUpdate(BaseModel):
    name: str | None = None
    url: HttpUrl | None = None
    auto_update: bool | None = None
    content: str | None = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        return _normalize_name(value, required=False)


class YamlPreviewRead(BaseModel):
    content: str


class TemplateSourceRead(BaseModel):
    id: int
    name: str
    kind: str


class TemplateSourceInput(BaseModel):
    kind: str | None = None
    id: int | None = Field(default=None, ge=1)

    @model_validator(mode='after')
    def validate_source(self) -> 'TemplateSourceInput':
        has_kind = self.kind is not None
        has_id = self.id is not None
        if has_kind != has_id:
            msg = 'template_source requires both kind and id'
            raise ValueError(msg)
        if self.kind is not None and self.kind not in {'template', 'composite'}:
            msg = 'template_source kind must be template or composite'
            raise ValueError(msg)
        return self


class MergeProfileTargetInput(BaseModel):
    compatibility_version: str
    template_id: int = Field(ge=1)


class MergeProfileTargetRead(ORMReadModel):
    id: int
    profile_id: int
    target: Literal['sing-box']
    compatibility_version: str
    template_id: int


class MergeProfileRead(BaseModel):
    id: int
    public_id: str
    name: str
    enabled: bool
    template_source: TemplateSourceRead | None
    subscriptions: list[SubscriptionSummaryRead]


class MergeProfileCreate(BaseModel):
    name: str = Field(min_length=1)
    template_source: TemplateSourceInput | None = None
    enabled: bool = True
    subscription_ids: list[int] = Field(min_length=1)

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        return str(_normalize_name(value, required=True))

    @field_validator('subscription_ids')
    @classmethod
    def validate_subscription_ids(cls, value: list[int]) -> list[int]:
        return list(_validate_subscription_ids(value, required=True) or [])


class MergeProfileUpdate(BaseModel):
    name: str | None = None
    template_source: TemplateSourceInput | None = None
    enabled: bool | None = None
    subscription_ids: list[int] | None = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        return _normalize_name(value, required=False)

    @field_validator('subscription_ids')
    @classmethod
    def validate_subscription_ids(cls, value: list[int] | None) -> list[int] | None:
        return _validate_subscription_ids(value, required=False)


__all__ = [
    'ConvertRequest',
    'MergeProfileCreate',
    'MergeProfileRead',
    'MergeProfileTargetInput',
    'MergeProfileTargetRead',
    'MergeProfileUpdate',
    'MergeRequest',
    'RuleSourceCreate',
    'RuleSourceRead',
    'RuleSourceUpdate',
    'SubscriptionCreate',
    'SubscriptionRead',
    'SubscriptionSourceInput',
    'SubscriptionSummaryRead',
    'SubscriptionUpdate',
    'TemplateCreate',
    'TemplateRead',
    'TemplateSourceInput',
    'TemplateSourceRead',
    'TemplateSummaryRead',
    'TemplateUpdate',
    'YamlPreviewRead',
    'validate_template_metadata',
]
