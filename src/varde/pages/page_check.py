"""Validate UI statements in page documents."""

from pathlib import Path

from varde.pages.fences import find_fences, ui_results
from varde.pages.include_statement import INCLUDE
from varde.ui.blocks.check import (
    COMPONENT_SPECS,
    INPUT_COMPONENTS,
    SPECS,
    BlockError,
    check_props,
)
from varde.ui.blocks.containers import container_errors

PAGE_SPECS = {**COMPONENT_SPECS, "include": INCLUDE}
CUSTOM_REMOVED = (
    "the `custom` block was removed; use `ui` components (`varde pages blocks`)"
)


# Fence languages that held page data before the line syntax: the TOML typed
# fences and the JSON `recap` and plain-text `deps` fences.
OLD_FENCES = frozenset(
    {*SPECS, *(n for n, s in COMPONENT_SPECS.items() if s.block_type == "status")}
)
TOML_FENCE_REMOVED = (
    "typed fences were replaced by `ui` statements; "
    "rewrite this one as a statement (`varde pages blocks <type>`) "
    "(for ordinary code, use another language tag)"
)


def _old_fence_errors(doc_text: str) -> list[BlockError]:
    return [
        BlockError(
            f.line, "toml-fence-removed", f"`{f.lang}` fence: {TOML_FENCE_REMOVED}"
        )
        for f in find_fences(doc_text, OLD_FENCES)
    ]


def _duplicate_id(
    ident: str, line: int, first_seen: dict[str, int]
) -> list[BlockError]:
    """An id already used by an earlier fence (the parser covers one fence)."""
    if ident in first_seen:
        message = (
            f"id '{ident}' is already used by the statement at line {first_seen[ident]}"
        )
        return [BlockError(line, "id-duplicate", message, ident)]
    first_seen[ident] = line
    return []


def _ui_errors(doc_text: str, root: Path | None) -> list[BlockError]:
    """Parse, props, include and heading-id errors for a document's `ui` text."""
    # Lazy: these import the page renderer, which imports this package.
    from varde.pages.include import include_errors
    from varde.pages.select import heading_id_errors

    errors: list[BlockError] = []
    first_seen: dict[str, int] = {}
    held: list[tuple[int, str, str, dict[str, object]]] = []
    for fence_line, result in ui_results(doc_text):
        errors += [
            BlockError(fence_line + e.line, e.rule, e.message) for e in result.errors
        ]
        for statement in result.statements:
            line = fence_line + statement.line
            errors += _duplicate_id(statement.id, line, first_seen)
            errors += check_props(
                statement.component,
                statement.props,
                line,
                statement.id,
                specs=PAGE_SPECS,
            )
            held.append((line, statement.component, statement.id, statement.props))
    errors += [BlockError(*found) for found in container_errors(held, INPUT_COMPONENTS)]
    found = include_errors(doc_text, root) + heading_id_errors(doc_text)
    errors += [BlockError(line, rule, message) for line, rule, message in found]
    return errors


def _custom_errors(doc_text: str) -> list[BlockError]:
    fences = find_fences(doc_text, frozenset({"custom"}))
    return [BlockError(f.line, "custom-block-removed", CUSTOM_REMOVED) for f in fences]


def check(doc_text: str, root: Path | None = None) -> list[BlockError]:
    """Return every block error in document order.

    `root` is the page's directory; with it each `include` source must resolve.
    """
    errors = _old_fence_errors(doc_text)
    errors += _ui_errors(doc_text, root)
    errors += _custom_errors(doc_text)
    return sorted(errors, key=lambda error: error.line)
