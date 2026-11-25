"""Keep status and selection indicators off individual vertical edges."""

import re
from pathlib import Path

from ui_paths import UI_STATIC_DIR

CSS_DIR = Path(__file__).resolve().parents[2] / "src/tavle/page/static/css"
UI_CSS_DIR = UI_STATIC_DIR / "css"
CSS_FILES = sorted(
    [*CSS_DIR.glob("*.css"), *UI_CSS_DIR.glob("*.css")], key=lambda p: p.name
)
ALLOW_EDGE_BORDERS = {
    ("01-base.css", "blockquote"): "Quote bar, same in every state",
    ("10-chrome.css", "blockquote"): "Quote bar, same in every state",
    (
        "40-table.css",
        ".vb-table-sticky th:first-child, .vb-table-sticky td:first-child",
    ): "Sticky column separator",
    (
        "40-table.css",
        ".vb-table-sticky .vb-group-head th:first-child",
    ): "Remove sticky column separator",
    (
        "40-table.css",
        (
            ".vb-table-stack.vb-cards.vb-table-sticky th:first-child, "
            ".vb-table-stack.vb-cards.vb-table-sticky td:first-child"
        ),
    ): "Remove separator in stacked layout",
    (
        "53-filetree.css",
        ".vd-file-tree-list .vd-file-tree-list",
    ): "Nested tree guide line, never changes with state",
    (
        "55-containers.css",
        ".vd-columns-panel",
    ): "Column separator between panels, never changes with state",
    (
        "59-timeline.css",
        ".vd-timeline-item::before",
    ): "Timeline connector line between items, never changes with state",
    (
        "59-timeline.css",
        ".vd-timeline-horizontal .vd-timeline-item::before",
    ): "Remove vertical connector in horizontal layout",
}
RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
EDGE = re.compile(
    r"^border-(?:left|right|inline-start|inline-end)(?:-(?:width|color|style))?$",
    re.IGNORECASE,
)


def edge_rules() -> list[tuple[str, str, str]]:
    rules = []
    for path in CSS_FILES:
        css = re.sub(r"/\*.*?\*/", "", path.read_text(), flags=re.DOTALL)
        for match in RULE.finditer(css):
            selector = match.group(1).strip()
            for declaration in match.group(2).split(";"):
                name, sep, value = declaration.partition(":")
                if sep and EDGE.fullmatch(name.strip()):
                    rules.append(
                        (path.name, selector, f"{name.strip()}: {value.strip()}")
                    )
    return rules


def test_no_status_edge_border() -> None:
    offenders = [
        f"{file}: {selector}: {declaration}"
        for file, selector, declaration in edge_rules()
        if (file, selector) not in ALLOW_EDGE_BORDERS
    ]
    assert not offenders, "\n" + "\n".join(offenders)


def test_allow_list_entries_match_rules() -> None:
    present = {(file, selector) for file, selector, _ in edge_rules()}
    assert not (ALLOW_EDGE_BORDERS.keys() - present), (
        ALLOW_EDGE_BORDERS.keys() - present
    )
