"""Store a page comment, suggestion, drift judgment or answer. No HTTP."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from varde_pages.actions import kind_allowed
from varde_pages.answers import answer_fields, validate_answer
from varde_pages.assemble import read_markdown
from varde_pages.comments import (
    ANSWER_KINDS,
    KINDS,
    append_comment,
    append_part_comment,
)
from varde_pages.include import IncludeError, IncludeSource, include_sources
from varde_pages.render import render_page
from varde_pages.validation import (
    MAX_ITEM,
    MAX_QUOTE,
    MAX_TEXT,
    parse_json_object,
    strings,
)

EDIT_OFF = "editing is off; serve with --allow-edit"


def _quote_of(data: dict[str, Any]) -> str:
    quote = data.get("quote")
    if quote is None:
        return ""
    if not isinstance(quote, str):
        raise ValueError("quote must be a string")  # noqa: TRY004
    return quote


def _kind_of(data: dict[str, Any]) -> str:
    kind = data.get("kind", "comment")
    if kind not in KINDS:
        raise ValueError("kind must be comment, suggestion, drift, decision or answer")
    return kind


def _replacement_of(data: dict[str, Any]) -> str:
    replacement = data.get("replacement", "")
    if not isinstance(replacement, str):
        raise ValueError("replacement must be a string")  # noqa: TRY004
    return replacement


def comment_fields(data: dict[str, Any]) -> tuple[str, str, str, str, str]:
    """Validate comment fields in a parsed body."""
    if data.get("kind") in {"suggestion", "drift", "decision", "answer"}:
        data = {"text": "", **data}
    anchor, text = strings(data, "anchor", "text")
    quote = _quote_of(data)
    kind = _kind_of(data)
    replacement = _replacement_of(data)
    if max(len(text), len(replacement)) > MAX_TEXT:
        raise ValueError(f"text longer than {MAX_TEXT} characters")
    if kind == "suggestion" and not (quote and len(quote) <= MAX_QUOTE):
        raise ValueError(f"suggestion needs a quote of 1-{MAX_QUOTE} characters")
    return (
        anchor,
        (quote if kind == "suggestion" else quote[:MAX_QUOTE]),
        text,
        kind,
        replacement,
    )


DRIFT_VERDICTS = ("accepted", "rejected", "open")


def drift_fields(data: dict[str, Any]) -> tuple[str, str]:
    """Validate the fields of a drift judgment."""
    item, verdict = strings(data, "item", "verdict")
    if not item or len(item) > MAX_ITEM:
        raise ValueError(f"drift item needs 1-{MAX_ITEM} characters")
    if verdict not in DRIFT_VERDICTS:
        raise ValueError("verdict must be accepted, rejected or open")
    return item, verdict


class DecisionDenied(PermissionError):
    """An answer was posted while editing is off."""

    def __init__(self) -> None:
        super().__init__(EDIT_OFF)


def _part_of(data: dict[str, Any]) -> str | None:
    """The `part` a comment body names, or None; ValueError for a non-string."""
    part = data.get("part")
    if part is None:
        return None
    if not isinstance(part, str) or not 0 < len(part) <= MAX_ITEM:
        raise ValueError("part must be an include id")
    return part


def sources_for(doc: Path, raw: bytes) -> Mapping[str, IncludeSource] | None:
    """The page's include sources when the body names a `part`, else None.

    Resolved on every call, so a source swapped after page load is re-checked
    at write time. A broken include is a ValueError (400), never a silent
    fallback to the page's own sidecar.
    """
    if _part_of(parse_json_object(raw)) is None:
        return None
    try:
        return include_sources(read_markdown(doc), doc.parent)
    except IncludeError as error:
        raise ValueError(str(error)) from error


def check_kind_allowed(doc: Path, anchor: str, kind: str) -> None:
    """Refuse a new row whose kind the anchor's block type cannot take.

    An anchor that no longer resolves is kept as an orphan `comment` only.
    Reads never call this, so old rows still fold and display.
    """
    blocks = render_page(read_markdown(doc), doc.name).blocks
    block_type = next((b.block_type for b in blocks if b.anchor == anchor), None)
    if block_type is None:
        if kind != "comment":
            raise ValueError(f"{kind} is not allowed on a block that no longer exists")
        return
    row_kind = "answer" if kind in ANSWER_KINDS else kind  # `decision` is the old name
    if not kind_allowed(block_type, row_kind):
        raise ValueError(f"{kind} is not allowed on {block_type}")


def _answer_text(value: object, item: str, text: str) -> str:
    shown = value if isinstance(value, str) else json.dumps(value)
    return text.strip() or f"{shown}: {item}"[:200]


def _store_answer(
    doc: Path,
    data: dict[str, Any],
    anchor: str,
    kind: str,
    decisions_open: bool,
) -> dict[str, Any]:
    if not decisions_open:
        raise DecisionDenied
    check_kind_allowed(doc, anchor, kind)
    item, value, text = answer_fields(data)
    validate_answer(read_markdown(doc), item, value, text)
    text = _answer_text(value, item, text)
    if kind == "decision":  # the old wire row, kept for pages served before `answer`
        extra = {"kind": kind, "item": item, "verdict": value}
    else:
        extra = {"kind": kind, "item": item, "value": value}
    return append_comment(doc, anchor, "", text, extra=extra)


def _comment_extra(
    data: dict[str, Any], kind: str, replacement: str, text: str
) -> tuple[dict[str, Any] | None, str]:
    """The extra row fields and the stored text of a comment, suggestion or drift."""
    extra = {"kind": kind, "replacement": replacement} if kind != "comment" else None
    if kind == "suggestion" and not text.strip():
        text = "Suggested edit"
    if kind == "drift":
        item, verdict = drift_fields(data)
        extra = {"kind": kind, "item": item, "verdict": verdict}
        text = text.strip() or f"{verdict}: {item}"
    return extra, text


def _store_part_comment(
    sources: Mapping[str, IncludeSource] | None,
    part: str,
    fields: tuple[str, str, str],
) -> dict[str, Any]:
    anchor, quote, text = fields
    if not text.strip():
        raise ValueError("empty comment text")
    source = (sources or {}).get(part)
    if source is None:
        raise ValueError(f"unknown part {part!r}")
    return append_part_comment(source, anchor, quote[:200], text)


def store_comment(
    doc: Path,
    raw: bytes,
    *,
    decisions_open: bool,
    sources: Mapping[str, IncludeSource] | None = None,
) -> dict[str, Any]:
    """Append the comment in a JSON body; raise ValueError or DecisionDenied.

    An answer is stored only when `decisions_open` is true; the caller decides,
    because the gate differs between `pages serve` and the daemon. Only a
    `comment` may carry `part`; it is appended to the sidecar of the included
    source `sources[part]`. Answers, suggestions and drift rows belong to the
    page and always go to its own sidecar.
    """
    data = parse_json_object(raw)
    anchor, quote, text, kind, replacement = comment_fields(data)
    part = _part_of(data)
    if part is not None and kind != "comment":
        raise ValueError("only a comment may name a part")
    if kind in ANSWER_KINDS:
        return _store_answer(doc, data, anchor, kind, decisions_open)
    if part is None:
        check_kind_allowed(doc, anchor, kind)
    extra, text = _comment_extra(data, kind, replacement, text)
    if part is None:
        return append_comment(doc, anchor, quote, text, extra=extra)
    return _store_part_comment(sources, part, (anchor, quote, text))
