"""Helpers for rewriting template rule-providers to project-served cached URLs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from ...db.models import RuleSource

if TYPE_CHECKING:
    from fastapi import Request
    from sqlalchemy.ext.asyncio import AsyncSession


async def build_cached_rule_provider_urls(db: AsyncSession, request: Request) -> dict[str, str]:
    sources = list((await db.scalars(select(RuleSource).order_by(RuleSource.id))).all())
    mappings: dict[str, str] = {}
    for source in sources:
        cached_url = str(request.url_for('get_cached_rule_provider', rule_source_id=source.id))
        mappings[source.name] = cached_url
        mappings[source.url] = cached_url
    return mappings


__all__ = ['build_cached_rule_provider_urls']
