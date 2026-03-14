from __future__ import annotations

from fastapi import APIRouter

from .composite_templates import router as composite_templates_router
from .config import router as config_router
from .convert import router as convert_router
from .merge import router as merge_router
from .merge_profiles import router as merge_profiles_router
from .rules import router as rules_router
from .template_patches import router as template_patches_router

api_router = APIRouter()
api_router.include_router(convert_router)
api_router.include_router(merge_router)
api_router.include_router(merge_profiles_router)
api_router.include_router(composite_templates_router)
api_router.include_router(template_patches_router)
api_router.include_router(config_router)
api_router.include_router(rules_router)

__all__ = ['api_router']
