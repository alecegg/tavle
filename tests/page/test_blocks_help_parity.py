"""The text help, index and JSON catalog of component specs."""

from __future__ import annotations

import re
from typing import Any

import pytest

from tavle import PAGE_SPECS, BlockSpec, PropertySpec, blocks

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


SHOWS = PropertySpec("shows", "string", nonempty=True)
DEMO = BlockSpec(
    "demo",
    "a demo",
    ("first line", "", "  indented  "),
    "d = demo()",
    lambda _: [],
    properties=(
        PropertySpec("title", "string", required=True, enum=("a", "b")),
        PropertySpec("n", "integer"),
    ),
    extra_keys=PropertySpec("state", "object", fields=(SHOWS,)),
)
PLAIN = BlockSpec("plain", "no fields", (), "p = plain()", lambda _: [])
SPECS = {"plain": PLAIN, "demo": DEMO}


def test_type_text_lays_out_fields_details_and_syntax() -> None:
    assert blocks.type_text(SPECS, "demo") == (
        "demo - a demo\n"
        "\n"
        "Fields:\n"
        "  title    required  string: a | b\n"
        "  n        optional  integer\n"
        "  <state>  optional  object\n"
        "    shows  optional  string, nonempty\n"
        "\n"
        "Details:\n"
        "  first line\n"
        "\n"
        "    indented\n"
        "\n"
        "Line syntax (in a ```ui fence):\n"
        "  d = demo()\n"
    )
    assert blocks.type_text(SPECS, "plain") == (
        "plain - no fields\n\nLine syntax (in a ```ui fence):\n  p = plain()\n"
    )


def test_index_text_lists_each_component_by_name() -> None:
    assert blocks.index_text(SPECS) == (
        "demo - a demo\n"
        "plain - no fields\n"
        "\n"
        "Fields and an example: varde pages blocks <TYPE>\n"
    )


def test_catalog_holds_every_named_component_as_plain_data() -> None:
    demo, plain = blocks.catalog(SPECS)
    assert demo["name"] == "demo"
    assert demo["extra_keys"] == {
        "name": "state",
        "type": "object",
        "required": False,
        "enum": (),
        "items": None,
        "fields": (
            {
                "name": "shows",
                "type": "string",
                "required": False,
                "enum": (),
                "items": None,
                "fields": (),
                "nonempty": True,
            },
        ),
        "nonempty": False,
    }
    assert plain == {
        "name": "plain",
        "summary": "no fields",
        "block_type": "visual",
        "properties": [],
        "extra_keys": None,
    }
    assert blocks.catalog(SPECS, ("plain",)) == [plain]
