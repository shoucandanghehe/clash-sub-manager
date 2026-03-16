"""Pydantic request and response models for the HTTP API."""

from __future__ import annotations

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


class SubscriptionSourceInput(BaseModel):
    url: HttpUrl | None = None
    content: str | None = None
    proxy: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    follow_redirects: bool = True

    @model_validator(mode='after')
    def validate_source(self) -> SubscriptionSourceInput:
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
        )


class ConvertRequest(SubscriptionSourceInput):
    template: dict[str, object] | None = None


class MergeRequest(BaseModel):
    configs: list[SubscriptionSourceInput] = Field(default_factory=list)
    template: dict[str, object] | None = None

    @model_validator(mode='after')
    def validate_configs(self) -> MergeRequest:
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
    enabled: bool
    template_id: int | None


class SubscriptionCreate(SubscriptionSourceInput):
    name: str = Field(min_length=1)
    enabled: bool = True
    template_id: int | None = None

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
    enabled: bool | None = None
    template_id: int | None = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        return _normalize_name(value, required=False)


class TemplateRead(ORMReadModel):
    id: int
    name: str
    content: str
    is_default: bool


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1)
    content: str
    is_default: bool = False

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        return str(_normalize_name(value, required=True))


class TemplateUpdate(BaseModel):
    name: str | None = None
    content: str | None = None
    is_default: bool | None = None

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


class MergeProfileRead(BaseModel):
    id: int
    name: str
    enabled: bool
    template_id: int | None
    template: TemplateSummaryRead | None
    subscriptions: list[SubscriptionSummaryRead]


class MergeProfileCreate(BaseModel):
    name: str = Field(min_length=1)
    template_id: int | None = None
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
    template_id: int | None = None
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
    'TemplateSummaryRead',
    'TemplateUpdate',
    'YamlPreviewRead',
]
