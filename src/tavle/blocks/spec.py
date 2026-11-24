"""The shape of one block type's definition."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from varde.ui.blocks.rules import Fault

# `any` checks presence only; the widget's own validator checks a value that may
# take more than one shape (for example a line given as n or "a-b").
PropertyType = Literal[
    "string", "integer", "number", "boolean", "list", "object", "id", "any"
]


@dataclass(frozen=True)
class PropertySpec:
    name: str
    type: PropertyType
    required: bool = False
    enum: tuple[str, ...] = ()
    items: PropertyType | None = None
    fields: tuple[PropertySpec, ...] = ()
    # a blank string or an empty list faults; applies to this value, not list items
    nonempty: bool = False

    def __post_init__(self) -> None:
        if self.nonempty and self.type not in ("string", "list"):
            raise ValueError("nonempty requires a string or a list")
        if self.items is not None and self.type != "list":
            raise ValueError("items requires a list")
        if self.fields and not (
            self.type == "object" or (self.type == "list" and self.items == "object")
        ):
            raise ValueError("fields requires an object or list of objects")
        if self.enum and not (
            self.type == "string" or (self.type == "list" and self.items == "string")
        ):
            raise ValueError("enum requires a string or list of strings")


@dataclass(frozen=True)
class BlockSpec:
    name: str
    summary: str
    # prose the help prints under "Details": meaning, defaults and behaviour that
    # `properties` cannot hold; the field lines themselves come from `properties`
    notes: tuple[str, ...]
    example: str  # one `ui` statement that validates; its id is the type name
    validate: Callable[[dict[str, object]], list[Fault]]
    # The page block type the component renders as (`data-block-type`): `widget`
    # and `decision` take an answer, `status` has no text to copy, `part` is
    # expanded to the parts it names.
    block_type: str = "visual"
    properties: tuple[PropertySpec, ...] = ()
    # every key not named in `properties` must match this (its name is unused);
    # None makes such a key unknown. ui-states takes any state name this way.
    extra_keys: PropertySpec | None = None


WIDGET = "widget"
DECISION = "decision"
INPUT_BLOCK_TYPES = frozenset({WIDGET, DECISION})


@dataclass(frozen=True)
class AnswerSchema:
    """What a component's answer row may hold; `validate_answer` checks against it."""

    kind: str  # type of `value`, for example "verdict"
    fields: tuple[str, ...]  # extra row fields the answer carries, for example "text"
    allowed: tuple[str, ...]  # accepted values; empty when any value of `kind` is
    # `form` only: the validated field tables the value is checked against
    shape: tuple[dict[str, object], ...] = ()
    # `number` only: (min, max, step) the value must lie in and sit on
    bounds: tuple[float, float, float] | None = None
