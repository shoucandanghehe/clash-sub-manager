"""Fetch remote subscription content with per-subscription network settings."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from ..models.subscription import SubscriptionConfig


class SubscriptionFetchError(RuntimeError):
    """Raised when a remote subscription fetch fails."""


class SubscriptionFetcher:
    def __init__(self, config: SubscriptionConfig):
        self.config = config

    async def fetch(self) -> str:
        """Return inline content or fetch the remote subscription body."""

        if self.config.content is not None:
            return self.config.content
        if self.config.url is None:
            msg = 'subscription has no fetchable source'
            raise SubscriptionFetchError(msg)

        try:
            async with httpx.AsyncClient(
                proxy=self.config.proxy,
                follow_redirects=self.config.follow_redirects,
                headers=self.config.headers,
            ) as client:
                response = await client.get(str(self.config.url))
                response.raise_for_status()
        except httpx.HTTPError as exc:
            msg = f'failed to fetch subscription {self.config.name!r}'
            raise SubscriptionFetchError(msg) from exc
        return response.text


__all__ = ['SubscriptionFetchError', 'SubscriptionFetcher']
