"""CRUD endpoints for composed templates."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...core import PatchValidationError, TemplateComposer
from ...db import CompositeTemplate, Template, TemplatePatch
from ..dependencies import get_db_session
from ..schemas import TemplateSummaryRead
from ..schemas_patch import (
    CompositePreviewRead,
    CompositeTemplateCreate,
    CompositeTemplatePreviewRequest,
    CompositeTemplateRead,
    CompositeTemplateUpdate,
    TemplatePatchSummaryRead,
)
from ._db import commit_or_name_conflict

router = APIRouter(tags=['composite-templates'])
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def _serialize_patch_summary(patch: TemplatePatch) -> TemplatePatchSummaryRead:
    return TemplatePatchSummaryRead.model_validate(patch)


def _serialize_composite_template(composite: CompositeTemplate, patches: list[TemplatePatch]) -> CompositeTemplateRead:
    return CompositeTemplateRead(
        id=composite.id,
        name=composite.name,
        base_template_id=composite.base_template_id,
        patch_sequence=list(composite.patch_sequence),
        cached_content=composite.cached_content,
        created_at=composite.created_at,
        updated_at=composite.updated_at,
        base_template=TemplateSummaryRead.model_validate(composite.base_template),
        patches=[_serialize_patch_summary(patch) for patch in patches],
    )


async def _get_template_or_404(db: AsyncSession, template_id: int) -> Template:
    template = await db.get(Template, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='template not found')
    return template


async def _get_patches_or_404(db: AsyncSession, patch_sequence: list[int]) -> list[TemplatePatch]:
    if not patch_sequence:
        return []

    unique_patch_ids = sorted(set(patch_sequence))
    patches = list((await db.scalars(select(TemplatePatch).where(TemplatePatch.id.in_(unique_patch_ids)))).all())
    patch_by_id = {patch.id: patch for patch in patches}
    missing_ids = [patch_id for patch_id in patch_sequence if patch_id not in patch_by_id]
    if missing_ids:
        missing = ', '.join(str(patch_id) for patch_id in dict.fromkeys(missing_ids))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'template patches not found: {missing}')
    return [patch_by_id[patch_id] for patch_id in patch_sequence]


async def _get_composite_template_or_404(composite_id: int, db: AsyncSession) -> CompositeTemplate:
    statement = (
        select(CompositeTemplate)
        .options(selectinload(CompositeTemplate.base_template))
        .where(CompositeTemplate.id == composite_id)
    )
    composite_template = (await db.scalars(statement)).one_or_none()
    if composite_template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='composite template not found')
    return composite_template


async def _render_cached_content(
    composite_template: CompositeTemplate,
    db: AsyncSession,
) -> tuple[str, list[TemplatePatch]]:
    patches = await _get_patches_or_404(db, composite_template.patch_sequence)
    try:
        cached_content = TemplateComposer().render_cached_content(composite_template.base_template, patches)
    except (PatchValidationError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return cached_content, patches


@router.get('/composite-templates', response_model=list[CompositeTemplateRead])
async def list_composite_templates(db: DbSession) -> list[CompositeTemplateRead]:
    statement = select(CompositeTemplate).options(selectinload(CompositeTemplate.base_template)).order_by(CompositeTemplate.id)
    composites = list((await db.scalars(statement)).all())

    changed = False
    serialized: list[CompositeTemplateRead] = []
    for composite in composites:
        cached_content, patches = await _render_cached_content(composite, db)
        if composite.cached_content != cached_content:
            composite.cached_content = cached_content
            changed = True
        serialized.append(_serialize_composite_template(composite, patches))

    if changed:
        await db.commit()
    return serialized


@router.post('/composite-templates', response_model=CompositeTemplateRead, status_code=status.HTTP_201_CREATED)
async def create_composite_template(payload: CompositeTemplateCreate, db: DbSession) -> CompositeTemplateRead:
    base_template = await _get_template_or_404(db, payload.base_template_id)
    patches = await _get_patches_or_404(db, payload.patch_sequence)

    try:
        cached_content = TemplateComposer().render_cached_content(base_template, patches)
    except (PatchValidationError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    composite = CompositeTemplate(
        name=payload.name,
        base_template_id=payload.base_template_id,
        patch_sequence=list(payload.patch_sequence),
        cached_content=cached_content,
    )
    composite.base_template = base_template
    db.add(composite)
    await commit_or_name_conflict(db, resource_name='composite template', table_name='composite_templates')
    await db.refresh(composite)
    return _serialize_composite_template(composite, patches)


@router.get('/composite-templates/{composite_id}', response_model=CompositeTemplateRead)
async def get_composite_template(composite_id: int, db: DbSession) -> CompositeTemplateRead:
    composite = await _get_composite_template_or_404(composite_id, db)
    cached_content, patches = await _render_cached_content(composite, db)
    if composite.cached_content != cached_content:
        composite.cached_content = cached_content
        await db.commit()
        await db.refresh(composite)
    return _serialize_composite_template(composite, patches)


@router.put('/composite-templates/{composite_id}', response_model=CompositeTemplateRead)
async def update_composite_template(
    composite_id: int,
    payload: CompositeTemplateUpdate,
    db: DbSession,
) -> CompositeTemplateRead:
    composite = await _get_composite_template_or_404(composite_id, db)

    name = payload.name if 'name' in payload.model_fields_set and payload.name is not None else composite.name
    base_template_id = (
        payload.base_template_id
        if 'base_template_id' in payload.model_fields_set and payload.base_template_id is not None
        else composite.base_template_id
    )
    patch_sequence = list(payload.patch_sequence) if payload.patch_sequence is not None else list(composite.patch_sequence)

    base_template = await _get_template_or_404(db, base_template_id)
    patches = await _get_patches_or_404(db, patch_sequence)

    try:
        cached_content = TemplateComposer().render_cached_content(base_template, patches)
    except (PatchValidationError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    composite.name = name
    composite.base_template_id = base_template_id
    composite.base_template = base_template
    composite.patch_sequence = patch_sequence
    composite.cached_content = cached_content

    await commit_or_name_conflict(db, resource_name='composite template', table_name='composite_templates')
    await db.refresh(composite)
    return _serialize_composite_template(composite, patches)


@router.delete('/composite-templates/{composite_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_composite_template(composite_id: int, db: DbSession) -> Response:
    composite = await _get_composite_template_or_404(composite_id, db)
    await db.delete(composite)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post('/composite-templates/preview', response_model=CompositePreviewRead)
async def preview_composite_template(payload: CompositeTemplatePreviewRequest, db: DbSession) -> CompositePreviewRead:
    base_template = await _get_template_or_404(db, payload.base_template_id)
    patches = await _get_patches_or_404(db, payload.patch_sequence)

    try:
        content = TemplateComposer().compose(base_template, patches)
        return CompositePreviewRead(content=content)
    except (PatchValidationError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
