"""SQLAlchemy ORM models for persisted subscriptions, templates, rules, merge profiles, and patch resources."""

from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .models_patch import CompositeTemplate, TemplatePatch

merge_profile_subscriptions = Table(
    'merge_profile_subscriptions',
    Base.metadata,
    Column('merge_profile_id', ForeignKey('merge_profiles.id', ondelete='CASCADE'), primary_key=True),
    Column('subscription_id', ForeignKey('subscriptions.id', ondelete='CASCADE'), primary_key=True),
)


class Template(Base):
    __tablename__ = 'templates'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    content: Mapped[str] = mapped_column(Text())
    is_default: Mapped[bool] = mapped_column(Boolean(), default=False)

    subscriptions: Mapped[list[Subscription]] = relationship(back_populates='template')
    merge_profiles: Mapped[list[MergeProfile]] = relationship(back_populates='template')
    composite_templates: Mapped[list[CompositeTemplate]] = relationship(back_populates='base_template')


class Subscription(Base):
    __tablename__ = 'subscriptions'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    content: Mapped[str | None] = mapped_column(Text(), nullable=True)
    proxy: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    headers: Mapped[dict[str, str]] = mapped_column(JSON(), default=dict)
    follow_redirects: Mapped[bool] = mapped_column(Boolean(), default=True)
    enabled: Mapped[bool] = mapped_column(Boolean(), default=True)
    template_id: Mapped[int | None] = mapped_column(ForeignKey('templates.id'), nullable=True)

    template: Mapped[Template | None] = relationship(back_populates='subscriptions')
    merge_profiles: Mapped[list[MergeProfile]] = relationship(
        secondary=merge_profile_subscriptions,
        back_populates='subscriptions',
    )


class RuleSource(Base):
    __tablename__ = 'rule_sources'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    url: Mapped[str] = mapped_column(String(2048))
    auto_update: Mapped[bool] = mapped_column(Boolean(), default=True)
    content: Mapped[str | None] = mapped_column(Text(), nullable=True)


class MergeProfile(Base):
    __tablename__ = 'merge_profiles'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    template_id: Mapped[int | None] = mapped_column(ForeignKey('templates.id'), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean(), default=True)

    template: Mapped[Template | None] = relationship(back_populates='merge_profiles')
    subscriptions: Mapped[list[Subscription]] = relationship(
        secondary=merge_profile_subscriptions,
        back_populates='merge_profiles',
        order_by='Subscription.id',
    )


__all__ = [
    'CompositeTemplate',
    'MergeProfile',
    'RuleSource',
    'Subscription',
    'Template',
    'TemplatePatch',
    'merge_profile_subscriptions',
]
