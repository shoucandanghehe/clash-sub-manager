"""HTTP endpoint for merging multiple subscriptions."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.merger import SubscriptionMerger
from ...core.template import TemplateProcessor
from ..dependencies import get_db_session
from ..schemas import MergeRequest  # noqa: TC001
from ._rule_providers import build_cached_rule_provider_urls

router = APIRouter(tags=['merge'])
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.post('/merge')
async def merge_subscriptions(payload: MergeRequest, request: Request, db: DbSession) -> dict[str, object]:
    subscriptions = [config.to_subscription_config(f'merge-{index}') for index, config in enumerate(payload.configs, start=1)]
    template = None
    if payload.template is not None:
        rule_provider_urls = await build_cached_rule_provider_urls(db, request)
        template = TemplateProcessor(payload.template, rule_provider_urls=rule_provider_urls)
    return await SubscriptionMerger(subscriptions).merge(template)
