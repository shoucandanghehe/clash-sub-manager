"""CRUD endpoints for subscriptions and templates."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.fetcher import SubscriptionFetcher
from ...db.models import CompositeTemplate, MergeProfileTarget, Subscription, Template
from ...models import SubscriptionConfig
from ...parsers import ProxyParser
from ..dependencies import get_db_session
from ..schemas import (
    SubscriptionCreate,
    SubscriptionRead,
    SubscriptionUpdate,
    TemplateCreate,
    TemplateRead,
    TemplateUpdate,
)
from ._db import commit_or_name_conflict

router = APIRouter(tags=['config'])


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get('/subscriptions', response_model=list[SubscriptionRead])
async def list_subscriptions(db: DbSession) -> list[Subscription]:
    return list((await db.scalars(select(Subscription).order_by(Subscription.id))).all())


@router.post('/subscriptions', response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED)
async def create_subscription(payload: SubscriptionCreate, db: DbSession) -> Subscription:
    subscription = Subscription(
        name=payload.name,
        url=str(payload.url) if payload.url is not None else None,
        content=payload.content,
        cached_content=None,
        last_updated_at=None,
        proxy=payload.proxy,
        headers=payload.headers,
        follow_redirects=payload.follow_redirects,
        timeout_seconds=payload.timeout_seconds,
        enabled=payload.enabled,
        excluded_node_names=payload.excluded_node_names,
    )
    db.add(subscription)
    await commit_or_name_conflict(db, resource_name='subscription', table_name='subscriptions')
    await db.refresh(subscription)
    return subscription


@router.get('/subscriptions/{subscription_id}', response_model=SubscriptionRead)
async def get_subscription(subscription_id: int, db: DbSession) -> Subscription:
    subscription = await db.get(Subscription, subscription_id)
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='subscription not found')
    return subscription


@router.put('/subscriptions/{subscription_id}', response_model=SubscriptionRead)
async def update_subscription(subscription_id: int, payload: SubscriptionUpdate, db: DbSession) -> Subscription:
    subscription = await db.get(Subscription, subscription_id)
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='subscription not found')

    current = {
        'name': subscription.name,
        'url': subscription.url,
        'content': subscription.content,
        'proxy': subscription.proxy,
        'headers': subscription.headers,
        'follow_redirects': subscription.follow_redirects,
        'timeout_seconds': subscription.timeout_seconds,
        'enabled': subscription.enabled,
        'excluded_node_names': subscription.excluded_node_names,
    }
    updated = payload.model_dump(exclude_unset=True)
    source_changed = (
        'url' in updated and (str(updated['url']) if updated['url'] is not None else None) != subscription.url
    ) or ('content' in updated and updated['content'] != subscription.content)
    merged = current | updated
    SubscriptionConfig.model_validate(
        {
            'name': merged['name'],
            'url': merged['url'],
            'content': merged['content'],
            'proxy': merged['proxy'],
            'headers': merged['headers'],
            'follow_redirects': merged['follow_redirects'],
            'timeout_seconds': merged['timeout_seconds'],
            'enabled': merged['enabled'],
            'excluded_node_names': merged['excluded_node_names'],
        }
    )
    for field, value in merged.items():
        if field == 'url' and value is not None:
            setattr(subscription, field, str(value))
        else:
            setattr(subscription, field, value)
    if source_changed:
        subscription.cached_content = None
        subscription.last_updated_at = None

    await commit_or_name_conflict(db, resource_name='subscription', table_name='subscriptions')
    await db.refresh(subscription)
    return subscription


@router.post('/subscriptions/{subscription_id}/update', response_model=SubscriptionRead)
async def refresh_subscription(subscription_id: int, db: DbSession) -> Subscription:
    subscription = await db.get(Subscription, subscription_id)
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='subscription not found')
    if subscription.url is None or subscription.content is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='inline subscription cannot be refreshed',
        )

    config = SubscriptionConfig.model_validate(
        {
            'name': subscription.name,
            'url': subscription.url,
            'content': None,
            'proxy': subscription.proxy,
            'headers': subscription.headers,
            'follow_redirects': subscription.follow_redirects,
            'timeout_seconds': subscription.timeout_seconds,
            'enabled': subscription.enabled,
        }
    )
    content = await SubscriptionFetcher(config).fetch()
    try:
        ProxyParser.parse_subscription(content)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    subscription.cached_content = content
    subscription.last_updated_at = _utc_now()
    await db.commit()
    await db.refresh(subscription)
    return subscription


@router.delete('/subscriptions/{subscription_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(subscription_id: int, db: DbSession) -> Response:
    subscription = await db.get(Subscription, subscription_id)
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='subscription not found')
    await db.delete(subscription)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/templates', response_model=list[TemplateRead])
async def list_templates(db: DbSession) -> list[Template]:
    return list((await db.scalars(select(Template).order_by(Template.id))).all())


@router.post('/templates', response_model=TemplateRead, status_code=status.HTTP_201_CREATED)
async def create_template(payload: TemplateCreate, db: DbSession) -> Template:
    template = Template(**payload.model_dump())
    db.add(template)
    await commit_or_name_conflict(db, resource_name='template', table_name='templates')
    await db.refresh(template)
    return template


@router.get('/templates/{template_id}', response_model=TemplateRead)
async def get_template(template_id: int, db: DbSession) -> Template:
    template = await db.get(Template, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='template not found')
    return template


@router.put('/templates/{template_id}', response_model=TemplateRead)
async def update_template(template_id: int, payload: TemplateUpdate, db: DbSession) -> Template:
    template = await db.get(Template, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='template not found')
    updated = payload.model_dump(exclude_unset=True)
    for field in ('target', 'schema_version', 'format'):
        if field in updated and updated[field] != getattr(template, field):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='template target metadata is immutable',
            )
    for field, value in updated.items():
        setattr(template, field, value)
    await commit_or_name_conflict(db, resource_name='template', table_name='templates')
    await db.refresh(template)
    return template


@router.delete('/templates/{template_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(template_id: int, db: DbSession) -> Response:
    template = await db.get(Template, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='template not found')
    target_binding = await db.scalar(select(MergeProfileTarget.id).where(MergeProfileTarget.template_id == template_id))
    if target_binding is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='template is used by a merge profile target',
        )

    composite_template = await db.scalar(
        select(CompositeTemplate.id).where(CompositeTemplate.base_template_id == template_id)
    )
    if composite_template is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='template is used by a composite template',
        )

    await db.delete(template)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
