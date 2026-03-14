"""SQLAlchemy ORM models for template patches and composed templates."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .models import Template


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TemplatePatch(Base):
    __tablename__ = 'template_patches'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    operations: Mapped[list[dict[str, object]]] = mapped_column(JSON(), default=list)
    created_at: Mapped[datetime] = mapped_column(default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(default=_utc_now, onupdate=_utc_now)


class CompositeTemplate(Base):
    __tablename__ = 'composite_templates'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    base_template_id: Mapped[int] = mapped_column(ForeignKey('templates.id'))
    patch_sequence: Mapped[list[int]] = mapped_column(JSON(), default=list)
    cached_content: Mapped[str] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(default=_utc_now, onupdate=_utc_now)

    base_template: Mapped[Template] = relationship(back_populates='composite_templates')


__all__ = ['CompositeTemplate', 'TemplatePatch']
