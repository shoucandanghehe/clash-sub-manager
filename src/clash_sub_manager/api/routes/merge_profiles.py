"""CRUD endpoints for persisted merge profiles."""

from __future__ import annotations

from typing import Annotated

import yaml
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...core.composer import TemplateComposer
from ...core.merger import SubscriptionMerger
from ...core.template import TemplateProcessor
from ...db.models import MergeProfile, Subscription, Template
from ...models import SubscriptionConfig
from ..dependencies import get_db_session
from ..schemas import (
    MergeProfileCreate,
    MergeProfileRead,
    MergeProfileUpdate,
    SubscriptionSummaryRead,
    TemplateSummaryRead,
    YamlPreviewRead,
 )
from ._db import commit_or_name_conflict
from ._rule_providers import build_cached_rule_provider_urls

router = APIRouter(tags=['merge-profiles'])
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def _get_template_or_404(db: AsyncSession, template_id: int | None) -> Template | None:
    if template_id is None:
        return None

    template = await db.get(Template, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='template not found')
    return template


async def _get_subscriptions_or_404(db: AsyncSession, subscription_ids: list[int]) -> list[Subscription]:
    subscriptions = list(
        (
            await db.scalars(
                select(Subscription)
                .where(Subscription.id.in_(subscription_ids))
                .order_by(Subscription.id),
            )
        ).all()
    )
    subscription_by_id = {subscription.id: subscription for subscription in subscriptions}
    missing_ids = [subscription_id for subscription_id in subscription_ids if subscription_id not in subscription_by_id]
    if missing_ids:
        missing = ', '.join(str(subscription_id) for subscription_id in missing_ids)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'subscriptions not found: {missing}')
    return [subscription_by_id[subscription_id] for subscription_id in subscription_ids]


async def _get_merge_profile_or_404(profile_id: int, db: AsyncSession) -> MergeProfile:
    statement = (
        select(MergeProfile)
        .options(
            selectinload(MergeProfile.template),
            selectinload(MergeProfile.subscriptions),
        )
        .where(MergeProfile.id == profile_id)
    )
    merge_profile = (await db.scalars(statement)).one_or_none()
    if merge_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='merge profile not found')
    return merge_profile


async def _build_merge_profile_document(
    merge_profile: MergeProfile,
    request: Request,
    db: AsyncSession,
) -> dict[str, object]:
    template = None
    if merge_profile.template is not None:
        rule_provider_urls = await build_cached_rule_provider_urls(db, request)
        template = TemplateProcessor(
            yaml.safe_load(merge_profile.template.content),
            rule_provider_urls=rule_provider_urls,
        )
    subscriptions = [_to_subscription_config(subscription) for subscription in merge_profile.subscriptions]
    return await SubscriptionMerger(subscriptions).merge(template)


def _serialize_merge_profile(merge_profile: MergeProfile) -> MergeProfileRead:
    ordered_subscriptions = sorted(merge_profile.subscriptions, key=lambda subscription: subscription.id)
    return MergeProfileRead(
        id=merge_profile.id,
        name=merge_profile.name,
        enabled=merge_profile.enabled,
        template_id=merge_profile.template_id,
        template=TemplateSummaryRead.model_validate(merge_profile.template) if merge_profile.template is not None else None,
        subscriptions=[SubscriptionSummaryRead.model_validate(subscription) for subscription in ordered_subscriptions],
    )


def _to_subscription_config(subscription: Subscription) -> SubscriptionConfig:
    return SubscriptionConfig.model_validate(
        {
            'name': subscription.name,
            'url': subscription.url,
            'content': subscription.content,
            'proxy': subscription.proxy,
            'headers': subscription.headers,
            'follow_redirects': subscription.follow_redirects,
            'enabled': subscription.enabled,
        }
    )


@router.get('/merge-profiles', response_model=list[MergeProfileRead])
async def list_merge_profiles(db: DbSession) -> list[MergeProfileRead]:
    statement = select(MergeProfile).options(
        selectinload(MergeProfile.template),
        selectinload(MergeProfile.subscriptions),
    )
    merge_profiles = list((await db.scalars(statement.order_by(MergeProfile.id))).all())
    return [_serialize_merge_profile(merge_profile) for merge_profile in merge_profiles]


@router.post('/merge-profiles', response_model=MergeProfileRead, status_code=status.HTTP_201_CREATED)
async def create_merge_profile(payload: MergeProfileCreate, db: DbSession) -> MergeProfileRead:
    await _get_template_or_404(db, payload.template_id)
    subscriptions = await _get_subscriptions_or_404(db, payload.subscription_ids)

    merge_profile = MergeProfile(name=payload.name, template_id=payload.template_id, enabled=payload.enabled)
    merge_profile.subscriptions = subscriptions
    db.add(merge_profile)
    await commit_or_name_conflict(db, resource_name='merge profile', table_name='merge_profiles')
    return _serialize_merge_profile(await _get_merge_profile_or_404(merge_profile.id, db))


@router.get('/merge-profiles/{profile_id}', response_model=MergeProfileRead)
async def get_merge_profile(profile_id: int, db: DbSession) -> MergeProfileRead:
    return _serialize_merge_profile(await _get_merge_profile_or_404(profile_id, db))


@router.put('/merge-profiles/{profile_id}', response_model=MergeProfileRead)
async def update_merge_profile(profile_id: int, payload: MergeProfileUpdate, db: DbSession) -> MergeProfileRead:
    merge_profile = await _get_merge_profile_or_404(profile_id, db)

    if 'name' in payload.model_fields_set:
        merge_profile.name = payload.name if payload.name is not None else merge_profile.name
    if 'enabled' in payload.model_fields_set:
        merge_profile.enabled = bool(payload.enabled)
    if 'template_id' in payload.model_fields_set:
        await _get_template_or_404(db, payload.template_id)
        merge_profile.template_id = payload.template_id
    if 'subscription_ids' in payload.model_fields_set:
        merge_profile.subscriptions = await _get_subscriptions_or_404(db, payload.subscription_ids or [])

    await commit_or_name_conflict(db, resource_name='merge profile', table_name='merge_profiles')
    return _serialize_merge_profile(await _get_merge_profile_or_404(profile_id, db))


@router.get('/merge-profiles/by-name/{profile_name}/config')
async def get_merge_profile_config(profile_name: str, request: Request, db: DbSession) -> Response:
    statement = (
        select(MergeProfile)
        .options(
            selectinload(MergeProfile.template),
            selectinload(MergeProfile.subscriptions),
        )
        .where(MergeProfile.name == profile_name)
    )
    merge_profile = (await db.scalars(statement)).one_or_none()
    if merge_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='merge profile not found')
    document = await _build_merge_profile_document(merge_profile, request, db)
    content = TemplateComposer.render_document(document)
    return Response(content=content, media_type='application/yaml')


@router.delete('/merge-profiles/{profile_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_merge_profile(profile_id: int, db: DbSession) -> Response:
    merge_profile = await _get_merge_profile_or_404(profile_id, db)
    await db.delete(merge_profile)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post('/merge-profiles/{profile_id}/generate', response_model=YamlPreviewRead)
async def generate_merge_profile(profile_id: int, request: Request, db: DbSession) -> YamlPreviewRead:
    merge_profile = await _get_merge_profile_or_404(profile_id, db)
    document = await _build_merge_profile_document(merge_profile, request, db)
    return YamlPreviewRead(content=TemplateComposer.render_document(document))
