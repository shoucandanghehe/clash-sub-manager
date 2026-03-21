"""CRUD endpoints for subscriptions and templates."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.models import CompositeTemplate, Subscription, Template
from ...models import SubscriptionConfig
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
        proxy=payload.proxy,
        headers=payload.headers,
        follow_redirects=payload.follow_redirects,
        enabled=payload.enabled,
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
        'enabled': subscription.enabled,
    }
    updated = payload.model_dump(exclude_unset=True)
    merged = current | updated
    SubscriptionConfig.model_validate(
        {
            'name': merged['name'],
            'url': merged['url'],
            'content': merged['content'],
            'proxy': merged['proxy'],
            'headers': merged['headers'],
            'follow_redirects': merged['follow_redirects'],
            'enabled': merged['enabled'],
        }
    )
    for field, value in merged.items():
        if field == 'url' and value is not None:
            setattr(subscription, field, str(value))
        else:
            setattr(subscription, field, value)

    await commit_or_name_conflict(db, resource_name='subscription', table_name='subscriptions')
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
    template = Template(name=payload.name, content=payload.content, is_default=payload.is_default)
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
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(template, field, value)
    await commit_or_name_conflict(db, resource_name='template', table_name='templates')
    await db.refresh(template)
    return template


@router.delete('/templates/{template_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(template_id: int, db: DbSession) -> Response:
    template = await db.get(Template, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='template not found')

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
