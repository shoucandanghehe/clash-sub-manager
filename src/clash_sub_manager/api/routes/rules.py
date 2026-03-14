"""CRUD endpoints for rule sources plus update/merged-rules management."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.rules import RuleManager
from ...db.models import RuleSource
from ..dependencies import get_db_session
from ..schemas import RuleSourceCreate, RuleSourceRead, RuleSourceUpdate
from ._db import commit_or_name_conflict

router = APIRouter(tags=['rules'])
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get('/rule-sources', response_model=list[RuleSourceRead])
async def list_rule_sources(db: DbSession) -> list[RuleSource]:
    return list((await db.scalars(select(RuleSource).order_by(RuleSource.id))).all())


@router.post('/rule-sources', response_model=RuleSourceRead, status_code=status.HTTP_201_CREATED)
async def create_rule_source(payload: RuleSourceCreate, db: DbSession) -> RuleSource:
    rule_source = RuleSource(
        name=payload.name,
        url=str(payload.url),
        auto_update=payload.auto_update,
        content=payload.content,
    )
    db.add(rule_source)
    await commit_or_name_conflict(db, resource_name='rule source', table_name='rule_sources')
    await db.refresh(rule_source)
    return rule_source


@router.get('/rule-sources/{rule_source_id}', response_model=RuleSourceRead)
async def get_rule_source(rule_source_id: int, db: DbSession) -> RuleSource:
    rule_source = await db.get(RuleSource, rule_source_id)
    if rule_source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='rule source not found')
    return rule_source


@router.put('/rule-sources/{rule_source_id}', response_model=RuleSourceRead)
async def update_rule_source(rule_source_id: int, payload: RuleSourceUpdate, db: DbSession) -> RuleSource:
    rule_source = await db.get(RuleSource, rule_source_id)
    if rule_source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='rule source not found')
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule_source, field, str(value) if field == 'url' and value is not None else value)
    await commit_or_name_conflict(db, resource_name='rule source', table_name='rule_sources')
    await db.refresh(rule_source)
    return rule_source


@router.post('/rule-sources/{rule_source_id}/update')
async def refresh_rule_source(rule_source_id: int, db: DbSession) -> str:
    rule_source = await db.get(RuleSource, rule_source_id)
    if rule_source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='rule source not found')
    return await RuleManager().update_rule_source(db, rule_source)


@router.get('/rule-providers/{rule_source_id}', response_class=PlainTextResponse)
async def get_cached_rule_provider(rule_source_id: int, db: DbSession) -> PlainTextResponse:
    rule_source = await db.get(RuleSource, rule_source_id)
    if rule_source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='rule source not found')

    content = rule_source.content
    if rule_source.auto_update or content is None:
        content = await RuleManager().update_rule_source(db, rule_source)
    return PlainTextResponse(content)


@router.get('/rules')
async def get_rules(db: DbSession, source_ids: Annotated[list[int] | None, Query()] = None) -> list[str]:
    return await RuleManager().get_rules(db, source_ids)


@router.delete('/rule-sources/{rule_source_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule_source(rule_source_id: int, db: DbSession) -> Response:
    rule_source = await db.get(RuleSource, rule_source_id)
    if rule_source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='rule source not found')
    await db.delete(rule_source)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
