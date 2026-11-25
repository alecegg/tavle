"""Server-side validation of an `answer` row against its component's own props.

The client names a block id, a value and a text; nothing it sends is trusted.
The block is looked up in the page text (a `ui` statement), its
`AnswerSchema` gives the value type and allowed set, and sizes are capped.
Pure functions; no I/O.
"""

from __future__ import annotations

import json
from typing import Any

from varde.pagelib.page.fences import ui_statements
from varde.ui import (
    COMPONENTS,
    CONTROLS,
    MAX_ITEM,
    MAX_TEXT,
    MAX_VALUE_JSON,
    AnswerSchema,
    allowed_value,
    check_form_value,
    check_props,
    check_slider_value,
    finite,
    ranking_value,
)

_TEXT_REQUIRED = {"commented"}  # a verdict that is only meaningful with a reason


def answer_fields(data: dict[str, Any]) -> tuple[str, object, str]:
    item, text = data.get("item"), data.get("text", "")
    if not isinstance(item, str) or not isinstance(text, str):
        raise ValueError("item and text must be strings")  # noqa: TRY004
    if "value" in data:
        return item, data["value"], text
    if data.get("kind") == "decision" and "verdict" in data:
        return item, data["verdict"], text
    raise ValueError("an answer needs a value")


def _statement_props(doc_text: str, item: str) -> tuple[str, dict[str, object]] | None:
    for _, statement in ui_statements(doc_text):
        if statement.id == item:
            faults = check_props(statement.component, statement.props, 0)
            return None if faults else (statement.component, statement.props)
    return None


def answer_schema(doc_text: str, item: str) -> AnswerSchema | None:
    """The schema of the answerable block `item`, or None when there is none."""
    found = _statement_props(doc_text, item)
    if found is None:
        return None
    component = COMPONENTS.get(found[0])
    if component is None or component.answer_schema is None:
        return None
    return component.answer_schema(found[1])


def _kind_ok(schema: AnswerSchema, value: object) -> bool:
    kind = schema.kind
    if kind == "form":
        check_form_value(schema.shape, value)
        return True
    if kind == "number":
        ok = finite(value)
        if ok and schema.bounds is not None:
            check_slider_value(schema.bounds, value)  # names the range or step
        return ok
    if kind == "ranking":
        return ranking_value(value, schema.allowed)
    if kind in {"verdict", "string", "list"}:
        return allowed_value(kind, value, schema.allowed)
    raise ValueError(f"answer kind {kind!r} is not supported")


def _check_value(schema: AnswerSchema, value: object) -> None:
    kind = schema.kind
    if not _kind_ok(schema, value):
        shown = f"one of {', '.join(schema.allowed)}" if schema.allowed else kind
        raise ValueError(f"value must be {shown}")
    members = value if isinstance(value, list) else [value]
    if any(isinstance(m, str) and CONTROLS.search(m) for m in members):
        raise ValueError("value holds control characters")
    if (
        len(json.dumps(value, ensure_ascii=kind not in {"form", "ranking"}))
        > MAX_VALUE_JSON
    ):
        raise ValueError("value too large")


def _check_answer_text(item: str, text: str) -> None:
    if not item or len(item) > MAX_ITEM:
        raise ValueError(f"answer item needs 1-{MAX_ITEM} characters")
    if len(text) > MAX_TEXT:
        raise ValueError(f"text longer than {MAX_TEXT} characters")
    if CONTROLS.search(text) or CONTROLS.search(item):
        raise ValueError("text holds control characters")


def validate_answer(doc_text: str, item: str, value: object, text: str) -> None:
    """Raise ValueError unless `item` is an answerable block and the answer fits it."""
    _check_answer_text(item, text)
    schema = answer_schema(doc_text, item)
    if schema is None:
        raise ValueError(f"unknown answer block {item!r}")
    _check_value(schema, value)
    if text.strip() and "text" not in schema.fields:
        raise ValueError(f"block {item!r} takes no text")
    needs_text = schema.kind == "verdict" and value in _TEXT_REQUIRED
    if needs_text and not text.strip():
        raise ValueError("a comment needs text")


def answer_value(row: dict) -> object:
    """The value of an answer row; an old `decision` row carries its verdict."""
    return row.get("value") if row.get("kind") == "answer" else row.get("verdict")
