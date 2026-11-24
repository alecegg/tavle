"""Validate typed blocks in a document. Pure: text in, errors out."""

from collections.abc import Mapping
from dataclasses import dataclass

from ..blocks.annotated_code import ANNOTATED_CODE
from ..blocks.backend import DATA_MODEL, ENDPOINT
from ..blocks.callout import CALLOUT
from ..blocks.change_summary import CHANGE_SUMMARY
from ..blocks.charts import CHART
from ..blocks.checklist import CHECKLIST
from ..blocks.code import CODE
from ..blocks.containers import COLUMNS, TABS
from ..blocks.decision import DECISION
from ..blocks.deps import DEPS
from ..blocks.diagrams import DIAGRAM
from ..blocks.diff import DIFF
from ..blocks.file_tree import FILE_TREE
from ..blocks.flow import FLOW
from ..blocks.image import IMAGE
from ..blocks.inputs import CHOICE, COMMENT, FORM
from ..blocks.inputs_ordered import RANKING, SLIDER
from ..blocks.option_matrix import MATRIX
from ..blocks.recap import RECAP
from ..blocks.risk import RISK
from ..blocks.rules import Fault
from ..blocks.screen_flow import SCREEN_FLOW
from ..blocks.screens import UI_STATES, WIREFRAME
from ..blocks.sequence import SEQUENCE
from ..blocks.spec import (
    INPUT_BLOCK_TYPES,
    WIDGET,
    BlockSpec,
    PropertySpec,
    PropertyType,
)
from ..blocks.state import STATE
from ..blocks.stats import STATS
from ..blocks.tables import TABLE
from ..blocks.timeline import TIMELINE
from ..lines.parse import ID_RULE

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
    component: str,
    props: dict[str, object],
    line: int,
    statement_id: str = "",
    specs: Mapping[str, BlockSpec] = COMPONENT_SPECS,
) -> list[BlockError]:
    """Errors for one parsed statement's props (parsed from a `ui` statement)."""
    spec = specs.get(component)
    if spec is None:
        known = ", ".join(sorted(specs))
        message = f"unknown component '{component}'; known: {known}"
        return [BlockError(line, "component-unknown", message, statement_id)]
    return props_errors(spec, props, line, statement_id)


def props_errors(
    spec: BlockSpec, props: dict[str, object], line: int, statement_id: str = ""
) -> list[BlockError]:
    data = dict(props)
    faults = _covers_faults(data)
    data.pop("covers", None)
    if spec.properties:
        faults += _property_faults(data, spec.properties, extra_keys=spec.extra_keys)
    faults += spec.validate(data)  # widget validators locate no property path
    return [BlockError(line, f.rule, f.message, statement_id, f.path) for f in faults]
