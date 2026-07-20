"""Models describing subscription inputs and fetch behavior."""

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


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
    excluded_node_names: list[str] = Field(default_factory=list)

    @field_validator('excluded_node_names')
    @classmethod
    def validate_excluded_node_names(cls, value: list[str]) -> list[str]:
        normalized = [name.strip() for name in value]
        if any(not name for name in normalized):
            msg = 'excluded node names must not be blank'
            raise ValueError(msg)
        if len(set(normalized)) != len(normalized):
            msg = 'excluded node names must be unique'
            raise ValueError(msg)
        return normalized

    @model_validator(mode='after')
    def validate_source(self) -> 'SubscriptionConfig':
        has_url = self.url is not None
        has_content = self.content is not None and self.content.strip() != ''
        if has_url == has_content:
            msg = 'exactly one of url or content must be provided'
            raise ValueError(msg)
        return self


__all__ = ['SubscriptionConfig']
