"""Compose base templates with ordered template patches."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

import yaml

from .patch import PatchEngine

if TYPE_CHECKING:
    from ..db import CompositeTemplate, Template, TemplatePatch


class TemplateComposer:
    """Build a derived template document from a base template and ordered patches."""

    def __init__(self, patch_engine: PatchEngine | None = None) -> None:
        self.patch_engine = patch_engine or PatchEngine()

    def compose(self, base_template: dict[str, object] | Template, patches: list[TemplatePatch]) -> dict[str, object]:
        composed = self._load_template_document(base_template)
        for patch in patches:
            composed = self.patch_engine.apply(composed, patch.operations)
        return composed

    @staticmethod
    def render_document(document: dict[str, object]) -> str:
        return yaml.safe_dump(document, allow_unicode=True, sort_keys=False)

    def render_cached_content(self, base_template: dict[str, object] | Template, patches: list[TemplatePatch]) -> str:
        document = self.compose(base_template, patches)
        return self.render_document(document)

    @staticmethod
    def _load_template_document(base_template: dict[str, object] | Template) -> dict[str, object]:
        if isinstance(base_template, dict):
            return deepcopy(base_template)

        document = yaml.safe_load(base_template.content)
        if not isinstance(document, dict):
            msg = 'template content must decode to a mapping'
            raise TypeError(msg)
        return document


__all__ = ['TemplateComposer']
