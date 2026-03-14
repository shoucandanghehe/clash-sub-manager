"""Shared database helpers for API routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def _is_unique_name_violation(exc: IntegrityError, *, table_name: str) -> bool:
    message = str(exc.orig).lower()
    return 'unique' in message and (
        f'{table_name}.name' in message or f'uq_{table_name}_name' in message
    )


async def commit_or_name_conflict(db: AsyncSession, *, resource_name: str, table_name: str) -> None:
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        if _is_unique_name_violation(exc, table_name=table_name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f'{resource_name} name already exists',
            ) from exc
        raise


__all__ = ['commit_or_name_conflict']
