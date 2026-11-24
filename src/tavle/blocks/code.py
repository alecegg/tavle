"""Block type for source listings: code."""

from varde.ui.blocks.rules import (
    Fault,
)
from varde.ui.blocks.spec import BlockSpec, PropertySpec


def _is_line(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _is_range(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(_is_line(n) for n in value)
        and value[0] <= value[1]
    )


def _lines_faults(data: dict[str, object]) -> list[Fault]:
    if "lines" not in data or _is_range(data["lines"]):
        return []
    return [Fault("type", "code: 'lines' must be [from, to] with 1 <= from <= to")]


def _mark_faults(data: dict[str, object]) -> list[Fault]:
    if "mark" not in data:
        return []
    mark = data["mark"]
    if (
        isinstance(mark, list)
        and mark
        and all(_is_line(m) or _is_range(m) for m in mark)
    ):
        return []
    return [Fault("type", "code: 'mark' must be a list of line numbers or [from, to]")]


def validate_code(data: dict[str, object]) -> list[Fault]:
    return _lines_faults(data) + _mark_faults(data)


CODE = BlockSpec(
    "code",
    "A source listing with line numbers, optional marked lines and a Copy button",
    (
        "title: file name or caption.",
        "lines: [from, to] shows only those lines, numbered from `from`.",
        "wrap: true wraps long lines instead of scrolling sideways.",
        "numbers: false hides the line-number gutter.",
        "mark: line numbers or [from, to] ranges to call out.",
        "language: python, js, ts, json or shell are highlighted; others show plain.",
        "source: the code, as one string.",
    ),
    r"""code = code(
  language: "python",
  title: "queue.py",
  source: "def push(item):\n    queue.append(item)\n",
  mark: [2],
)
""",
    validate_code,
    block_type="code",
    properties=(
        PropertySpec("language", "string", required=True, nonempty=True),
        PropertySpec("source", "string", required=True, nonempty=True),
        PropertySpec("title", "string", nonempty=True),
        PropertySpec("lines", "any"),
        PropertySpec("wrap", "boolean"),
        PropertySpec("numbers", "boolean"),
        PropertySpec("mark", "any"),
    ),
)
