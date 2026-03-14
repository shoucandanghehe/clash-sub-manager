"""CRUD endpoints for template patches."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core import PatchValidationError, TemplateComposer
from ...db import CompositeTemplate, Template, TemplatePatch
from ..dependencies import get_db_session
from ..schemas_patch import (
    CompositePreviewRead,
    PatchOperation,
    TemplatePatchCreate,
    TemplatePatchPreviewRequest,
    TemplatePatchRead,
    TemplatePatchUpdate,
)
from ._db import commit_or_name_conflict

router = APIRouter(tags=['template-patches'])
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def _serialize_operations(payload_operations: list[PatchOperation]) -> list[dict[str, object]]:
    return [operation.model_dump(exclude_unset=True) for operation in payload_operations]


async def _get_template_or_404(db: AsyncSession, template_id: int) -> Template:
    template = await db.get(Template, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='template not found')
    return template


async def _get_template_patch_or_404(db: AsyncSession, patch_id: int) -> TemplatePatch:
    patch = await db.get(TemplatePatch, patch_id)
    if patch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='template patch not found')
    return patch


async def _get_composites_using_patch(db: AsyncSession, patch_id: int) -> list[CompositeTemplate]:
    composites = list((await db.scalars(select(CompositeTemplate).order_by(CompositeTemplate.id))).all())
    return [composite for composite in composites if patch_id in composite.patch_sequence]


@router.get('/template-patches', response_model=list[TemplatePatchRead])
async def list_template_patches(db: DbSession) -> list[TemplatePatch]:
    return list((await db.scalars(select(TemplatePatch).order_by(TemplatePatch.id))).all())


@router.post('/template-patches', response_model=TemplatePatchRead, status_code=status.HTTP_201_CREATED)
async def create_template_patch(payload: TemplatePatchCreate, db: DbSession) -> TemplatePatch:
    patch = TemplatePatch(
        name=payload.name,
        description=payload.description,
        operations=_serialize_operations(payload.operations),
    )
    db.add(patch)
    await commit_or_name_conflict(db, resource_name='template patch', table_name='template_patches')
    await db.refresh(patch)
    return patch


@router.get('/template-patches/{patch_id}', response_model=TemplatePatchRead)
async def get_template_patch(patch_id: int, db: DbSession) -> TemplatePatch:
    return await _get_template_patch_or_404(db, patch_id)


@router.put('/template-patches/{patch_id}', response_model=TemplatePatchRead)
async def update_template_patch(patch_id: int, payload: TemplatePatchUpdate, db: DbSession) -> TemplatePatch:
    patch = await _get_template_patch_or_404(db, patch_id)

    if 'name' in payload.model_fields_set:
        patch.name = payload.name if payload.name is not None else patch.name
    if 'description' in payload.model_fields_set:
        patch.description = payload.description
    if 'operations' in payload.model_fields_set and payload.operations is not None:
        patch.operations = _serialize_operations(payload.operations)

    await commit_or_name_conflict(db, resource_name='template patch', table_name='template_patches')
    await db.refresh(patch)
    return patch


@router.delete('/template-patches/{patch_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_template_patch(patch_id: int, db: DbSession) -> Response:
    patch = await _get_template_patch_or_404(db, patch_id)
    used_by = await _get_composites_using_patch(db, patch_id)
    if used_by:
        names = ', '.join(composite.name for composite in used_by)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'template patch is used by composite templates: {names}',
        )
    await db.delete(patch)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post('/template-patches/{patch_id}/preview', response_model=CompositePreviewRead)
async def preview_template_patch(
    patch_id: int,
    payload: TemplatePatchPreviewRequest,
    db: DbSession,
) -> CompositePreviewRead:
    patch = await _get_template_patch_or_404(db, patch_id)
    base_template = await _get_template_or_404(db, payload.base_template_id)

    try:
        content = TemplateComposer().compose(base_template, [patch])
        return CompositePreviewRead(content=content)
    except (PatchValidationError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
