"""Remote rule-source fetching, caching, and merge helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
from sqlalchemy import select

from ..db.models import RuleSource

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sqlalchemy.ext.asyncio import AsyncSession

class RuleUpdateError(RuntimeError):
    """Raised when rule-source refresh fails."""


class RuleManager:
    """Manage database-backed rule sources and cached merged rules."""

    async def fetch_remote_content(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        proxy: str | None = None,
        follow_redirects: bool = True,
    ) -> str:
        try:
            async with httpx.AsyncClient(
                proxy=proxy,
                headers=headers or {},
                follow_redirects=follow_redirects,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            msg = f'failed to fetch rules from {url!r}'
            raise RuleUpdateError(msg) from exc
        return response.text

    async def update_rule_source(self, session: AsyncSession, source: RuleSource) -> str:
        content = await self.fetch_remote_content(source.url)
        source.content = content
        await session.commit()
        await session.refresh(source)
        return content

    async def get_rules(self, session: AsyncSession, source_ids: list[int] | None = None) -> list[str]:
        query = select(RuleSource).order_by(RuleSource.id)
        if source_ids is not None:
            query = query.where(RuleSource.id.in_(source_ids))
        sources = list((await session.scalars(query)).all())
        if not sources:
            return []

        contents: list[str] = []
        for source in sources:
            if source.auto_update or source.content is None:
                contents.append(await self.update_rule_source(session, source))
            else:
                contents.append(source.content)
        return self.merge_rule_sets(self.parse_rules(content) for content in contents)

    @staticmethod
    def parse_rules(content: str) -> list[str]:
        rules: list[str] = []
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue
            rules.append(line)
        return rules

    @staticmethod
    def merge_rule_sets(rule_sets: Iterable[Iterable[str]]) -> list[str]:
        merged: list[str] = []
        seen: set[str] = set()
        for rule_set in rule_sets:
            for rule in rule_set:
                if rule in seen:
                    continue
                seen.add(rule)
                merged.append(rule)
        return merged


__all__ = ['RuleManager', 'RuleUpdateError']
