"""Block type for a source file with notes anchored to line ranges: annotated-code."""

import re

from ..blocks.rules import Fault
from ..blocks.spec import BlockSpec, PropertySpec

KINDS = ("info", "warn", "change")
MAX_NOTES = 40
MAX_NOTES_PER_LINE = 6
_RANGE = re.compile(r"\s*(\d+)\s*(?:-\s*(\d+))?\s*")


def source_line_count(source: str) -> int:
    """Lines the code panel shows for this source (a closing newline adds none)."""
    lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return len(lines) - 1 if len(lines) > 1 and not lines[-1] else len(lines)


def parse_range(value: object) -> tuple[int, int] | None:
    """`5`, `"5"` or `"5-6"` as (from, to); None when it is not a valid range."""
    if isinstance(value, bool):
        return None
    text = str(value) if isinstance(value, int) else value
    match = _RANGE.fullmatch(text) if isinstance(text, str) else None
    if not match:
        return None
    low = int(match[1])
    high = int(match[2] or low)
    return (low, high) if 1 <= low <= high else None


def _note_faults(note: object, where: str, total: int) -> list[Fault]:
    if not isinstance(note, dict) or "lines" not in note:
        return []
    faults: list[Fault] = []
    span = parse_range(note["lines"])
    if span is None:
        return faults + [Fault("type", f"{where}: lines must be n or 'from-to'")]
    if span[1] > total:
        faults.append(
            Fault("range", f"{where}: lines {span[0]}-{span[1]} pass line {total}")
        )
    return faults


def _crowded_faults(notes: list[object]) -> list[Fault]:
    starts: dict[int, int] = {}
    for note in notes:
        span = parse_range(note.get("lines")) if isinstance(note, dict) else None
        if span:
            starts[span[0]] = starts.get(span[0], 0) + 1
    return [
        Fault(
            "limit",
            f"annotated-code: more than {MAX_NOTES_PER_LINE} notes start at line {n}",
        )
        for n, count in sorted(starts.items())
        if count > MAX_NOTES_PER_LINE
    ]


def _notes_faults(data: dict[str, object]) -> list[Fault]:
    notes = data.get("notes")
    if not isinstance(notes, list):
        return []
    faults: list[Fault] = []
    if len(notes) > MAX_NOTES:
        faults.append(Fault("limit", f"annotated-code: at most {MAX_NOTES} notes"))
    source = data.get("source")
    total = source_line_count(source) if isinstance(source, str) else 0
    for i, note in enumerate(notes, 1):
        faults += _note_faults(note, f"annotated-code: notes[{i}]", total)
    return faults + _crowded_faults(notes)


def validate_annotated_code(data: dict[str, object]) -> list[Fault]:
    return _notes_faults(data)


ANNOTATED_CODE = BlockSpec(
    "annotated-code",
    "A source file with notes on line ranges; quiet stretches fold away",
    (
        "filename: file name shown in the header.",
        "language: python, js, ts, json or shell are highlighted; others show plain.",
        "source: the code, as one string.",
        "notes: up to 40; lines is n or 'a-b' inside the source; kind defaults to",
        "  info (the others are warn and change).",
        "collapse: false shows every line; by default stretches of 4 or more lines",
        "  that are more than 3 lines from any note are folded.",
    ),
    r"""annotated-code = annotated-code(
  filename: "queue.py",
  language: "python",
  source: "def push(item):\n    queue.append(item)\n",
  notes: [
    {"lines": 2, "label": "Unbounded", "note": "`queue` has no limit.", "kind": "warn"},
  ],
)
""",
    validate_annotated_code,
    properties=(
        PropertySpec("filename", "string", required=True, nonempty=True),
        PropertySpec("language", "string", required=True, nonempty=True),
        PropertySpec("source", "string", required=True, nonempty=True),
        PropertySpec("collapse", "boolean"),
        PropertySpec(
            "notes",
            "list",
            required=True,
            items="object",
            fields=(
                PropertySpec("lines", "any", required=True),
                PropertySpec("note", "string", required=True, nonempty=True),
                PropertySpec("label", "string", nonempty=True),
                PropertySpec("kind", "string", enum=KINDS),
            ),
        ),
    ),
)
