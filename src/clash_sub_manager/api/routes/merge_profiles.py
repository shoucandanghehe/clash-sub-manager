"""CRUD endpoints for persisted merge profiles."""

import asyncio
import json
from datetime import datetime, timezone
from typing import Annotated

import yaml
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...core.composer import TemplateComposer
from ...core.fetcher import SubscriptionFetcher, SubscriptionFetchError
from ...core.merger import SubscriptionMerger
from ...core.rules import RuleManager, RuleUpdateError
from ...core.singbox import (
    RULE_SET_VERSION,
    SING_BOX_COMPATIBILITY_VERSION,
    SING_BOX_SCHEMA_VERSION,
    RuleSetSourceSpec,
    SingBox113Renderer,
    SingBoxArtifactStore,
    SingBoxBinaryUnavailableError,
    SingBoxConfigValidationError,
    SingBoxRenderError,
    SingBoxRenderResult,
    SingBoxValidator,
)
from ...core.template import TemplateProcessor
from ...db import CompositeTemplate, MergeProfile, MergeProfileTarget, RuleSource, Subscription, Template
from ...models import SubscriptionConfig
from ..dependencies import get_db_session
from ..schemas import (
    MergeProfileCreate,
    MergeProfileRead,
    MergeProfileTargetInput,
    MergeProfileTargetRead,
    MergeProfileUpdate,
    SubscriptionSummaryRead,
    TemplateSourceInput,
    TemplateSourceRead,
    YamlPreviewRead,
)
from ._db import commit_or_name_conflict
from ._rule_providers import build_cached_rule_provider_urls

router = APIRouter(tags=['merge-profiles'])
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
_SHA256_HEX_LENGTH = 64


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def _get_template_or_404(db: AsyncSession, template_id: int | None) -> Template | None:
    if template_id is None:
        return None

    template = await db.get(Template, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='template not found')
    return template


async def _get_composite_template_or_404(
    db: AsyncSession,
    composite_template_id: int | None,
) -> CompositeTemplate | None:
    if composite_template_id is None:
        return None

    composite_template = await db.get(CompositeTemplate, composite_template_id)
    if composite_template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='composite template not found')
    return composite_template


async def _get_subscriptions_or_404(db: AsyncSession, subscription_ids: list[int]) -> list[Subscription]:
    subscriptions = list(
        (
            await db.scalars(
                select(Subscription).where(Subscription.id.in_(subscription_ids)).order_by(Subscription.id),
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
            selectinload(MergeProfile.composite_template),
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
    source_content = (
        merge_profile.template.content
        if merge_profile.template is not None
        else merge_profile.composite_template.cached_content
        if merge_profile.composite_template is not None
        else None
    )
    if source_content is not None:
        rule_provider_urls = await build_cached_rule_provider_urls(db, request)
        template = TemplateProcessor(
            yaml.safe_load(source_content),
            rule_provider_urls=rule_provider_urls,
        )
    resolved_configs = await _resolve_merge_profile_configs(merge_profile, db)
    return await SubscriptionMerger(resolved_configs).merge(template)


async def _resolve_merge_profile_configs(
    merge_profile: MergeProfile,
    db: AsyncSession,
) -> list[SubscriptionConfig]:
    resolved_subscriptions = await asyncio.gather(
        *(_resolve_subscription_config(subscription) for subscription in merge_profile.subscriptions)
    )
    configs = [config for config, _ in resolved_subscriptions]

    refreshed_at = _utc_now()
    cache_changed = False
    for subscription, (_, fetched_content) in zip(merge_profile.subscriptions, resolved_subscriptions, strict=True):
        if fetched_content is None:
            continue
        subscription.cached_content = fetched_content
        subscription.last_updated_at = refreshed_at
        cache_changed = True
    if cache_changed:
        await db.commit()
    return configs


async def _render_merge_profile_content(
    merge_profile: MergeProfile,
    request: Request,
    db: AsyncSession,
) -> str:
    try:
        document = await _build_merge_profile_document(merge_profile, request, db)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    return TemplateComposer.render_document(document)


def _serialize_template_source(merge_profile: MergeProfile) -> TemplateSourceRead | None:
    if merge_profile.template is not None:
        return TemplateSourceRead(id=merge_profile.template.id, name=merge_profile.template.name, kind='template')
    if merge_profile.composite_template is not None:
        return TemplateSourceRead(
            id=merge_profile.composite_template.id,
            name=merge_profile.composite_template.name,
            kind='composite',
        )
    return None


def _serialize_merge_profile(merge_profile: MergeProfile) -> MergeProfileRead:
    ordered_subscriptions = sorted(merge_profile.subscriptions, key=lambda subscription: subscription.id)
    return MergeProfileRead(
        id=merge_profile.id,
        public_id=merge_profile.public_id,
        name=merge_profile.name,
        enabled=merge_profile.enabled,
        template_source=_serialize_template_source(merge_profile),
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
            'timeout_seconds': subscription.timeout_seconds,
            'enabled': subscription.enabled,
            'excluded_node_names': subscription.excluded_node_names,
        }
    )


def _to_inline_subscription_config(config: SubscriptionConfig, content: str) -> SubscriptionConfig:
    if not content.strip():
        msg = f'subscription {config.name!r} content must not be empty'
        raise ValueError(msg)
    return SubscriptionConfig(
        name=config.name,
        content=content,
        proxy=config.proxy,
        headers=config.headers,
        follow_redirects=config.follow_redirects,
        timeout_seconds=config.timeout_seconds,
        enabled=config.enabled,
        excluded_node_names=config.excluded_node_names,
    )


async def _resolve_subscription_config(subscription: Subscription) -> tuple[SubscriptionConfig, str | None]:
    config = _to_subscription_config(subscription)
    if not config.enabled or config.content is not None:
        return config, None

    try:
        fetched_content = await SubscriptionFetcher(config).fetch()
    except SubscriptionFetchError:
        if subscription.cached_content is None:
            raise
        return _to_inline_subscription_config(config, subscription.cached_content), None

    if not fetched_content.strip():
        if subscription.cached_content is None:
            msg = f'subscription {config.name!r} content must not be empty'
            raise ValueError(msg)
        return _to_inline_subscription_config(config, subscription.cached_content), None

    return _to_inline_subscription_config(config, fetched_content), fetched_content


async def _apply_template_source(
    db: AsyncSession,
    merge_profile: MergeProfile,
    template_source: TemplateSourceInput | None,
) -> None:
    if template_source is None:
        merge_profile.template = None
        merge_profile.template_id = None
        merge_profile.composite_template = None
        merge_profile.composite_template_id = None
        return

    if template_source.kind == 'template':
        template = await _get_template_or_404(db, template_source.id)
        if template is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='template not found')
        if template.target != 'mihomo':
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail='legacy merge profile templates must target mihomo',
            )
        merge_profile.template = template
        merge_profile.template_id = template.id
        merge_profile.composite_template = None
        merge_profile.composite_template_id = None
        return

    composite_template = await _get_composite_template_or_404(db, template_source.id)
    if composite_template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='composite template not found')
    merge_profile.composite_template = composite_template
    merge_profile.composite_template_id = composite_template.id
    merge_profile.template = None
    merge_profile.template_id = None


@router.get('/merge-profiles')
async def list_merge_profiles(db: DbSession) -> list[MergeProfileRead]:
    statement = select(MergeProfile).options(
        selectinload(MergeProfile.template),
        selectinload(MergeProfile.composite_template),
        selectinload(MergeProfile.subscriptions),
    )
    merge_profiles = list((await db.scalars(statement.order_by(MergeProfile.id))).all())
    return [_serialize_merge_profile(merge_profile) for merge_profile in merge_profiles]


@router.post('/merge-profiles', status_code=status.HTTP_201_CREATED)
async def create_merge_profile(payload: MergeProfileCreate, db: DbSession) -> MergeProfileRead:
    subscriptions = await _get_subscriptions_or_404(db, payload.subscription_ids)

    merge_profile = MergeProfile(name=payload.name, enabled=payload.enabled)
    await _apply_template_source(db, merge_profile, payload.template_source)
    merge_profile.subscriptions = subscriptions
    db.add(merge_profile)
    await commit_or_name_conflict(db, resource_name='merge profile', table_name='merge_profiles')
    return _serialize_merge_profile(await _get_merge_profile_or_404(merge_profile.id, db))


@router.get('/merge-profiles/{profile_id}')
async def get_merge_profile(profile_id: int, db: DbSession) -> MergeProfileRead:
    return _serialize_merge_profile(await _get_merge_profile_or_404(profile_id, db))


@router.put('/merge-profiles/{profile_id}')
async def update_merge_profile(profile_id: int, payload: MergeProfileUpdate, db: DbSession) -> MergeProfileRead:
    merge_profile = await _get_merge_profile_or_404(profile_id, db)

    if 'name' in payload.model_fields_set:
        merge_profile.name = payload.name if payload.name is not None else merge_profile.name
    if 'enabled' in payload.model_fields_set:
        merge_profile.enabled = bool(payload.enabled)
    if 'template_source' in payload.model_fields_set:
        await _apply_template_source(db, merge_profile, payload.template_source)
    if 'subscription_ids' in payload.model_fields_set:
        merge_profile.subscriptions = await _get_subscriptions_or_404(db, payload.subscription_ids or [])

    await commit_or_name_conflict(db, resource_name='merge profile', table_name='merge_profiles')
    return _serialize_merge_profile(await _get_merge_profile_or_404(profile_id, db))


@router.put('/merge-profiles/{profile_id}/targets/sing-box', response_model=MergeProfileTargetRead)
async def upsert_sing_box_target(
    profile_id: int,
    payload: MergeProfileTargetInput,
    db: DbSession,
) -> MergeProfileTarget:
    await _get_merge_profile_or_404(profile_id, db)
    template = await _get_template_or_404(db, payload.template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='template not found')
    if template.target != 'sing-box':
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail='template target must be sing-box',
        )
    if template.schema_version != '1.13':
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail='sing-box template schema version must be 1.13',
        )
    if template.format != 'json':
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail='sing-box template format must be json',
        )
    if payload.compatibility_version != '1.13.14':
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail='sing-box compatibility version must be 1.13.14',
        )

    binding = await db.scalar(
        select(MergeProfileTarget).where(
            MergeProfileTarget.profile_id == profile_id,
            MergeProfileTarget.target == 'sing-box',
        )
    )
    if binding is None:
        binding = MergeProfileTarget(
            profile_id=profile_id,
            target='sing-box',
            compatibility_version=payload.compatibility_version,
            template_id=payload.template_id,
        )
        db.add(binding)
    else:
        binding.compatibility_version = payload.compatibility_version
        binding.template_id = payload.template_id
    await db.commit()
    await db.refresh(binding)
    return binding


async def _get_sing_box_profile(
    public_id: str,
    db: AsyncSession,
) -> tuple[MergeProfile, MergeProfileTarget]:
    merge_profile = (
        await db.scalars(
            select(MergeProfile)
            .options(selectinload(MergeProfile.subscriptions))
            .where(MergeProfile.public_id == public_id)
        )
    ).one_or_none()
    if merge_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='merge profile not found')
    binding = (
        await db.scalars(
            select(MergeProfileTarget)
            .options(selectinload(MergeProfileTarget.template))
            .where(
                MergeProfileTarget.profile_id == merge_profile.id,
                MergeProfileTarget.target == 'sing-box',
            )
        )
    ).one_or_none()
    if binding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='sing-box target not found')
    return merge_profile, binding


async def _resolve_sing_box_rule_sources(
    specs: tuple[RuleSetSourceSpec, ...],
    db: AsyncSession,
) -> dict[str, str]:
    source_names = {spec.source for spec in specs}
    sources = list((await db.scalars(select(RuleSource).where(RuleSource.name.in_(source_names)))).all())
    source_by_name = {source.name: source for source in sources}
    missing = sorted(source_names - set(source_by_name))
    if missing:
        message = f'rule sources not found: {", ".join(missing)}'
        raise SingBoxRenderError(message)
    contents: dict[str, str] = {}
    for name in source_names:
        source = source_by_name[name]
        if source.content is None:
            contents[name] = await RuleManager().update_rule_source(db, source)
        else:
            contents[name] = source.content
    return contents


async def _render_sing_box_profile(
    merge_profile: MergeProfile,
    binding: MergeProfileTarget,
    request: Request,
    db: AsyncSession,
) -> SingBoxRenderResult:
    validator: SingBoxValidator | None = request.app.state.sing_box_validator
    if validator is None:
        message = 'sing-box validator is not configured'
        raise SingBoxBinaryUnavailableError(message)
    store: SingBoxArtifactStore = request.app.state.sing_box_store
    renderer = SingBox113Renderer()
    specs = renderer.required_rule_sources(binding.template.content)
    rule_source_contents = await _resolve_sing_box_rule_sources(specs, db)
    configs = await _resolve_merge_profile_configs(merge_profile, db)
    resolution = await SubscriptionMerger(configs).resolve()
    result = renderer.render(
        binding.template.content,
        resolution.nodes,
        rule_source_contents,
        lambda digest: str(request.url_for('get_sing_box_rule_set', digest=digest)),
        dropped_nodes=resolution.dropped_nodes,
    )
    for artifact in result.rule_sets:
        await asyncio.to_thread(validator.check_rule_set, artifact.content, store.root / 'tmp')
    for artifact in result.rule_sets:
        store.publish_rule_set(artifact)
    await asyncio.to_thread(validator.check, result.content, store.root / 'tmp')
    store.publish_config(merge_profile.public_id, result.content)
    return result


@router.get('/api/v1/merge-profiles/{public_id}/targets/sing-box/config.json')
async def get_sing_box_profile_config(
    public_id: str,
    request: Request,
    db: DbSession,
    compat: Annotated[str, Query()],
) -> Response:
    if compat != SING_BOX_COMPATIBILITY_VERSION:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f'sing-box compatibility version must be {SING_BOX_COMPATIBILITY_VERSION}',
        )
    merge_profile, binding = await _get_sing_box_profile(public_id, db)
    template = binding.template
    if binding.compatibility_version != compat:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='target version mismatch')
    if template.target != 'sing-box' or template.schema_version != SING_BOX_SCHEMA_VERSION or template.format != 'json':
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='target template metadata mismatch'
        )

    try:
        result = await _render_sing_box_profile(merge_profile, binding, request, db)
    except SingBoxBinaryUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except RuleUpdateError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except (SingBoxConfigValidationError, SingBoxRenderError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    response_headers = {
        'X-CSM-Warning-Count': str(len(result.warnings)),
        'X-CSM-Dropped-Node-Count': str(len(result.dropped_nodes)),
    }
    if result.warnings:
        response_headers['X-CSM-Warnings'] = f'tls.insecure={len(result.warnings)}'
    if result.dropped_nodes:
        response_headers['X-CSM-Dropped-Nodes'] = json.dumps(result.dropped_nodes, ensure_ascii=True)
    return Response(content=result.content, media_type='application/json', headers=response_headers)


@router.get('/api/v1/sing-box/rule-sets/v4/{digest}.json', name='get_sing_box_rule_set')
async def get_sing_box_rule_set(digest: str, request: Request) -> Response:
    if len(digest) != _SHA256_HEX_LENGTH or any(character not in '0123456789abcdef' for character in digest):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='rule-set not found')
    store: SingBoxArtifactStore = request.app.state.sing_box_store
    path = store.rule_set_path(digest)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='rule-set not found')
    return Response(
        content=path.read_bytes(),
        media_type='application/json',
        headers={'Cache-Control': 'public, max-age=31536000, immutable', 'X-Rule-Set-Version': str(RULE_SET_VERSION)},
    )


@router.get('/merge-profiles/by-name/{profile_name}/config')
async def get_merge_profile_config(profile_name: str, request: Request, db: DbSession) -> Response:
    statement = (
        select(MergeProfile)
        .options(
            selectinload(MergeProfile.template),
            selectinload(MergeProfile.composite_template),
            selectinload(MergeProfile.subscriptions),
        )
        .where(MergeProfile.name == profile_name)
    )
    merge_profile = (await db.scalars(statement)).one_or_none()
    if merge_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='merge profile not found')
    content = await _render_merge_profile_content(merge_profile, request, db)
    return Response(content=content, media_type='application/yaml')


@router.delete('/merge-profiles/{profile_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_merge_profile(profile_id: int, db: DbSession) -> Response:
    merge_profile = await _get_merge_profile_or_404(profile_id, db)
    await db.execute(delete(MergeProfileTarget).where(MergeProfileTarget.profile_id == profile_id))
    await db.delete(merge_profile)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post('/merge-profiles/{profile_id}/generate')
async def generate_merge_profile(profile_id: int, request: Request, db: DbSession) -> YamlPreviewRead:
    merge_profile = await _get_merge_profile_or_404(profile_id, db)
    content = await _render_merge_profile_content(merge_profile, request, db)
    return YamlPreviewRead(content=content)
