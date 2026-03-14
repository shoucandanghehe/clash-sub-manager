"""Models describing subscription inputs and fetch behavior."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class SubscriptionConfig(BaseModel):
    """A single subscription source.

    Exactly one of ``url`` or ``content`` must be provided so callers can tell
    whether the manager is expected to fetch remotely or use inline content.
    """

    model_config = ConfigDict(extra='forbid')

    name: str
    url: HttpUrl | None = None
    content: str | None = None
    proxy: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    follow_redirects: bool = True
    enabled: bool = True

    @model_validator(mode='after')
    def validate_source(self) -> SubscriptionConfig:
        has_url = self.url is not None
        has_content = self.content is not None and self.content.strip() != ''
        if has_url == has_content:
            msg = 'exactly one of url or content must be provided'
            raise ValueError(msg)
        return self


__all__ = ['SubscriptionConfig']
