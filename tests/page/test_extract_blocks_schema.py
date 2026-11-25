"""Page fence scanning and rendering of component examples."""

import pytest
from ui_fence import example_fence

from tavle import blocks
from tavle.lines import parse_lines
from tavle.page.fences import Fence, _id_text, find_fences
from tavle.page.markdown_syntax import FENCE
from tavle.page.page_check import check
from tavle.page.render import render_page


def reference_find_fences(text, langs):
    """The scanner as it was before `scan_fences` (pinned for the differential test)."""
    lines = text.expandtabs(4).splitlines()
    found, i = [], 0
    while i < len(lines):
        opening = FENCE.match(lines[i])
        if opening is None:
            i += 1
            continue
        indent, marker, lang = len(opening.group(1)), opening.group(2), opening.group(3)
        body, j = [], i + 1
        while j < len(lines) and not (
            (closing := FENCE.match(lines[j]))
            and closing.group(2)[0] == marker[0]
            and len(closing.group(2)) >= len(marker)
            and not closing.group(3)
            and not closing.group(4).strip()
        ):
            body.append(lines[j][min(indent, len(lines[j]) - len(lines[j].lstrip())) :])
            j += 1
        if lang in langs:
            found.append(
                Fence(lang, i + 1, _id_text(opening.group(4)), "\n".join(body))
            )
        i = j + 1
    return found


def test_find_fences_matches_the_reference_scanner():
    import random

    rng = random.Random(7)  # noqa: S311 - test data
    pieces = [
        "```",
        "~~~",
        "````",
        "decision",
        "ui",
        "id=a",
        "  ",
        "\t",
        "x = 1",
        "",
        "text",
        " id=b",
    ]
    for _ in range(3000):
        lines = [
            "".join(rng.choices(pieces, k=rng.randint(0, 4)))
            for _ in range(rng.randint(0, 9))
        ]
        text = rng.choice(["\n", "\r\n"]).join(lines)
        langs = frozenset({"decision", "ui", ""})
        assert find_fences(text, langs) == reference_find_fences(text, langs)


@pytest.mark.parametrize("name", sorted(blocks.COMPONENT_SPECS))
def test_every_component_example_is_one_valid_statement_that_renders(name):
    spec = blocks.COMPONENT_SPECS[name]
    (statement,) = parse_lines(spec.example).statements
    assert statement.id == name and statement.component == name
    doc = example_fence(spec.example)
    # a container's example names ids that other statements of a real page hold
    assert [e for e in check(doc) if not e.rule.startswith("container-")] == []
    assert "vb-error" not in render_page(doc, "t.md").body
