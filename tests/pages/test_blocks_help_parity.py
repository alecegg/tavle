"""The text help of a component lists the properties its JSON catalog entry has."""

from __future__ import annotations

import re
from typing import Any

import pytest
from tavle import blocks

from varde.pages.page_check import PAGE_SPECS

FIELD_LINE = re.compile(r"^( *)(\S+) +(required|optional) +(.+)$")


def field_rows(text: str) -> list[tuple[int, str, str, str]]:
    """(depth, name, need, type text) of every line under `Fields:` in the help."""
    section = text.split("Fields:\n", 1)[1].split("\n\n", 1)[0]
    rows = []
    for line in section.splitlines():
        match = FIELD_LINE.match(line)
        assert match, line
        indent, name, need, rest = match.groups()
        rows.append((len(indent) // 2 - 1, name, need, rest))
    return rows


def json_rows(
    props: list[dict[str, Any]], depth: int = 0
) -> list[tuple[int, str, str, str]]:
    rows: list[tuple[int, str, str, str]] = []
    for prop in props:
        kind = f"list of {prop['items']}" if prop["items"] else str(prop["type"])
        kind += ", nonempty" if prop["nonempty"] else ""
        kind += f": {' | '.join(prop['enum'])}" if prop["enum"] else ""
        need = "required" if prop["required"] else "optional"
        rows.append((depth, str(prop["name"]), need, kind))
        rows += json_rows(prop["fields"], depth + 1)
    return rows


def expected_rows(entry: dict[str, Any]) -> list[tuple[int, str, str, str]]:
    rows = json_rows(entry["properties"])
    extra = entry["extra_keys"]
    if extra:
        (row, *nested) = json_rows([extra])
        rows += [(row[0], f"<{row[1]}>", *row[2:]), *nested]
    return rows


@pytest.mark.parametrize(
    "entry",
    blocks.catalog(
        PAGE_SPECS,
    ),
    ids=lambda e: str(e["name"]),
)
def test_help_lists_every_json_property(entry: dict[str, Any]) -> None:
    text = blocks.type_text(PAGE_SPECS, str(entry["name"]))
    assert field_rows(text) == expected_rows(entry)


def test_every_widget_has_a_property_in_the_json() -> None:
    assert all(
        entry["properties"]
        for entry in blocks.catalog(
            PAGE_SPECS,
        )
    )
