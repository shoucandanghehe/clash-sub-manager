"""HTTP endpoint for converting a single source into Clash output."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.composer import TemplateComposer
from ...core.merger import SubscriptionMerger
from ...core.template import TemplateProcessor
from ..dependencies import get_db_session
from ..schemas import ConvertRequest, YamlPreviewRead  # noqa: TC001
from ._rule_providers import build_cached_rule_provider_urls

router = APIRouter(tags=['convert'])
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.post('/convert', response_model=YamlPreviewRead)
async def convert_subscription(payload: ConvertRequest, request: Request, db: DbSession) -> YamlPreviewRead:
    subscription = payload.to_subscription_config('convert')
    template = None
    if payload.template is not None:
        rule_provider_urls = await build_cached_rule_provider_urls(db, request)
        template = TemplateProcessor(payload.template, rule_provider_urls=rule_provider_urls)
    document = await SubscriptionMerger([subscription]).merge(template)
    return YamlPreviewRead(content=TemplateComposer.render_document(document))
