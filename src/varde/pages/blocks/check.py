"""Validate typed blocks in a document. Pure: text in, errors out."""

from dataclasses import dataclass
from pathlib import Path

from varde.base.ui_lines.parse import ID_RULE
from varde.pages.blocks.annotated_code import ANNOTATED_CODE
from varde.pages.blocks.backend import DATA_MODEL, ENDPOINT
from varde.pages.blocks.callout import CALLOUT
from varde.pages.blocks.change_summary import CHANGE_SUMMARY
from varde.pages.blocks.charts import CHART
from varde.pages.blocks.checklist import CHECKLIST
from varde.pages.blocks.code import CODE
from varde.pages.blocks.containers import COLUMNS, TABS, container_errors
from varde.pages.blocks.decision import DECISION
from varde.pages.blocks.deps import DEPS
from varde.pages.blocks.diagrams import DIAGRAM
from varde.pages.blocks.diff import DIFF
from varde.pages.blocks.fences import find_fences, ui_results
from varde.pages.blocks.file_tree import FILE_TREE
from varde.pages.blocks.flow import FLOW
from varde.pages.blocks.image import IMAGE
from varde.pages.blocks.include import INCLUDE
from varde.pages.blocks.inputs import CHOICE, COMMENT, FORM
from varde.pages.blocks.inputs_ordered import RANKING, SLIDER
from varde.pages.blocks.option_matrix import MATRIX
from varde.pages.blocks.recap import RECAP
from varde.pages.blocks.risk import RISK
from varde.pages.blocks.rules import Fault
from varde.pages.blocks.screen_flow import SCREEN_FLOW
from varde.pages.blocks.screens import UI_STATES, WIREFRAME
from varde.pages.blocks.sequence import SEQUENCE
from varde.pages.blocks.spec import (
    INPUT_BLOCK_TYPES,
    WIDGET,
    BlockSpec,
    PropertySpec,
    PropertyType,
)
from varde.pages.blocks.state import STATE
from varde.pages.blocks.stats import STATS
from varde.pages.blocks.tables import TABLE
from varde.pages.blocks.timeline import TIMELINE

SPECS: dict[str, BlockSpec] = {
    s.name: s
    for s in (DATA_MODEL, ENDPOINT, WIREFRAME, UI_STATES, FLOW, TABLE, CHART, DECISION)
}
# Every component a `ui` statement may name.
COMPONENT_SPECS: dict[str, BlockSpec] = {
    **SPECS,
    "recap": RECAP,
    "deps": DEPS,
    "diagram": DIAGRAM,
    "include": INCLUDE,
    "choice": CHOICE,
    "form": FORM,
    "comment": COMMENT,
    "ranking": RANKING,
    "slider": SLIDER,
    "callout": CALLOUT,
    "code": CODE,
    "annotated-code": ANNOTATED_CODE,
    "file-tree": FILE_TREE,
    "diff": DIFF,
    "checklist": CHECKLIST,
    "stats": STATS,
    "timeline": TIMELINE,
    "tabs": TABS,
    "columns": COLUMNS,
    "matrix": MATRIX,
    "sequence": SEQUENCE,
    "risks": RISK,
    "state": STATE,
    "screen-flow": SCREEN_FLOW,
    "image": IMAGE,
    "change-summary": CHANGE_SUMMARY,
}
# Components whose inputs must stay visible, so a tab cannot hide them.
INPUT_COMPONENTS = frozenset(
    name for name, s in COMPONENT_SPECS.items() if s.block_type in INPUT_BLOCK_TYPES
)
# Inputs that ask an open question (all but the decision block).
OPEN_CHOICES = frozenset(
    name for name, s in COMPONENT_SPECS.items() if s.block_type == WIDGET
)
CUSTOM_REMOVED = (
    "the `custom` block was removed; use `ui` components (`varde pages blocks`)"
)


@dataclass(frozen=True)
class BlockError:
    line: int  # 1-based document line
    rule: str
    message: str
    statement_id: str = ""  # the `ui` statement id; empty when none applies
    path: str = ""  # property path such as `rows[2].name`; empty when none applies

    def text(self) -> str:
        return f"line {self.line}: {self.rule}: {self.message}"


def _covers_faults(data: dict[str, object]) -> list[Fault]:
    covers = data.get("covers")
    if covers is None:
        return []
    ok = isinstance(covers, list) and all(
        isinstance(c, str) and ID_RULE.match(c) for c in covers
    )
    if ok:
        return []
    return [Fault("covers", "covers must be a list of block ids", "covers")]


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
                statement.component, statement.props, line, statement.id
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


def _property_faults(
    data: dict[str, object],
    properties: tuple[PropertySpec, ...],
    prefix: str = "",
    extra_keys: PropertySpec | None = None,
) -> list[Fault]:
    names = {prop.name for prop in properties}
    faults: list[Fault] = []
    for key in sorted(data.keys() - names):
        path = f"{prefix}{key}"
        if extra_keys is None:
            faults.append(Fault("unknown-key", f"unknown key '{path}'", path))
            continue
        faults += _value_faults(data[key], extra_keys.type, path, extra_keys)
    for prop in properties:
        path = f"{prefix}{prop.name}"
        if prop.name not in data:
            if prop.required:
                faults.append(
                    Fault("missing-key", f"missing required key '{path}'", path)
                )
            continue
        faults += _value_faults(data[prop.name], prop.type, path, prop)
    return faults


def _is_empty(value: object) -> bool:
    return value == [] or (isinstance(value, str) and not value.strip())


def _value_faults(
    value: object, kind: PropertyType, path: str, prop: PropertySpec
) -> list[Fault]:
    valid = {
        "string": lambda: isinstance(value, str),
        "integer": lambda: isinstance(value, int) and not isinstance(value, bool),
        "number": lambda: (
            isinstance(value, int | float) and not isinstance(value, bool)
        ),
        "boolean": lambda: isinstance(value, bool),
        "list": lambda: isinstance(value, list),
        "object": lambda: isinstance(value, dict),
        "id": lambda: isinstance(value, str) and bool(ID_RULE.fullmatch(value)),
        "any": lambda: True,
    }
    if not valid[kind]():
        return [Fault("type", f"'{path}' must be {kind}", path)]
    faults: list[Fault] = []
    if prop.nonempty and _is_empty(value):
        return [Fault("type", f"'{path}' must not be empty", path)]
    if kind == "string" and prop.enum and value not in prop.enum:
        message = f"'{path}' must be one of {', '.join(prop.enum)}"
        faults.append(Fault("type", message, path))
    if kind == "object" and isinstance(value, dict) and prop.fields:
        faults += _property_faults(value, prop.fields, f"{path}.")
    if kind == "list" and isinstance(value, list) and prop.items:
        # each element is one value of the items type, never the list itself
        element = PropertySpec(
            prop.name, prop.items, enum=prop.enum, fields=prop.fields
        )
        # 1-based, as every widget message counts
        for index, item in enumerate(value, 1):
            faults += _value_faults(item, prop.items, f"{path}[{index}]", element)
    return faults


def check_props(
    component: str, props: dict[str, object], line: int, statement_id: str = ""
) -> list[BlockError]:
    """Errors for one parsed statement's props (parsed from a `ui` statement)."""
    spec = COMPONENT_SPECS.get(component)
    if spec is None:
        known = ", ".join(sorted(COMPONENT_SPECS))
        message = f"unknown component '{component}'; known: {known}"
        return [BlockError(line, "component-unknown", message, statement_id)]
    data = dict(props)
    faults = _covers_faults(data)
    data.pop("covers", None)
    if spec.properties:
        faults += _property_faults(data, spec.properties, extra_keys=spec.extra_keys)
    faults += spec.validate(data)  # widget validators locate no property path
    return [BlockError(line, f.rule, f.message, statement_id, f.path) for f in faults]
