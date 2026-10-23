"""CRUD endpoints for rule sources plus update/merged-rules management."""

from __future__ import annotations

import asyncio
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.rules import RuleManager, RuleUpdateError
from ...core.singbox import (
    RULE_SET_VERSION,
    SING_BOX_SCHEMA_VERSIONS,
    SingBoxArtifactStore,
    SingBoxBinaryUnavailableError,
    SingBoxConfigValidationError,
    SingBoxRenderer,
    SingBoxRenderError,
    SingBoxValidator,
)
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
    updated = payload.model_dump(exclude_unset=True)
    url_changed = 'url' in updated and str(updated['url']) != rule_source.url
    content_changed = 'content' in updated and updated['content'] != rule_source.content
    for field, value in updated.items():
        setattr(rule_source, field, str(value) if field == 'url' and value is not None else value)
    if url_changed and 'content' not in updated:
        rule_source.content = None
    if url_changed or content_changed:
        rule_source.last_updated_at = None
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


@router.get(
    '/api/v1/sing-box/rule-providers/{rule_source_id}/{behavior}.json',
    name='get_sing_box_rule_provider',
)
async def get_sing_box_rule_provider(
    rule_source_id: int,
    behavior: Literal['classical', 'domain', 'ipcidr'],
    request: Request,
    db: DbSession,
    compat: Annotated[str, Query()],
) -> Response:
    if compat not in SING_BOX_SCHEMA_VERSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f'sing-box compatibility version must be {" or ".join(SING_BOX_SCHEMA_VERSIONS)}',
        )
    validators: dict[str, SingBoxValidator] = request.app.state.sing_box_validators
    validator = validators.get(compat)
    if validator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f'sing-box validator for {compat} is not configured',
        )
    rule_source = await db.get(RuleSource, rule_source_id)
    if rule_source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='rule source not found')
    store: SingBoxArtifactStore = request.app.state.sing_box_store
    try:
        content = rule_source.content
        if rule_source.auto_update or content is None:
            content = await RuleManager().update_rule_source(db, rule_source)
        artifact = await asyncio.to_thread(SingBoxRenderer.compile_rule_set, content, behavior)
        await asyncio.to_thread(validator.check_rule_set, artifact.content, store.root / 'tmp')
    except RuleUpdateError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except SingBoxBinaryUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except (SingBoxConfigValidationError, SingBoxRenderError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    return Response(
        content=artifact.content,
        media_type='application/json',
        headers={'X-Rule-Set-Version': str(RULE_SET_VERSION)},
    )


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
