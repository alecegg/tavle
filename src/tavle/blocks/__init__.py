"""Typed visual blocks: registry, schemas and validation (renderers come later)."""

from varde.ui.blocks.check import (
    COMPONENT_SPECS,
    SPECS,
    BlockError,
    check_props,
    props_errors,
)
from varde.ui.blocks.reference import catalog, index_text, type_text

TYPES: tuple[str, ...] = tuple(sorted(SPECS))

__all__ = [
    "COMPONENT_SPECS",
    "SPECS",
    "TYPES",
    "BlockError",
    "catalog",
    "check_props",
    "index_text",
    "props_errors",
    "type_text",
]
