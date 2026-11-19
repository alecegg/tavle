"""Props for the diff component (`static/components/diff.js`).

The server does what needs `difflib`, a patch parser or the lexer: rows come from
`blocks.diff_rows`, folded into blocks, each row carrying its highlighted tokens.
The component draws the unified and side-by-side tables from them.
"""

import hashlib
import json
from dataclasses import dataclass

from varde.pages.blocks.annotated_code import parse_range
from varde.pages.blocks.diff_rows import (
    MAX_ROWS,
    Block,
    Row,
    change_word,
    diff_rows,
    layout,
    patch_rows,
    text_lines,
    unified_text,
)
from varde.pages.blocks_render.code import CLASS_OF, split_lines, tokenize

MAX_DIGIT_CLASS = 6


@dataclass(frozen=True)
class Note:
    number: int
    side: str
    start: int
    end: int
    text: str

    @property
    def where(self) -> str:
        lines = (
            f"line {self.start}"
            if self.start == self.end
            else f"lines {self.start}-{self.end}"
        )
        return f"{self.side} {lines}"


def read_notes(data: dict[str, object]) -> list[Note]:
    """Notes numbered in the author's order."""
    notes: list[Note] = []
    for raw in data.get("notes") or []:  # type: ignore[attr-defined]
        span = parse_range(raw.get("lines"))
        if span is None:
            continue
        notes.append(
            Note(len(notes) + 1, raw["side"], span[0], span[1], str(raw["note"]))
        )
    return notes


def anchored(notes: list[Note]) -> set[tuple[str, int]]:
    return {(n.side, line) for n in notes for line in range(n.start, n.end + 1)}


def _count_text(rows: list[Row]) -> str:
    added = sum(1 for r in rows if r.kind == "add")
    removed = sum(1 for r in rows if r.kind == "del")
    if not added and not removed:
        return "No changes"
    return f"+{added} added, -{removed} removed"


def _token_rows(
    rows: tuple[Row, ...], codes: dict[int, list[list[str]]]
) -> list[dict[str, object]]:
    return [
        {
            "kind": r.kind,
            "old": r.old,
            "new": r.new,
            "text": r.text,
            "code": codes[id(r)],
        }
        for r in rows
    ]


def _row_tokens(rows: list[Row], language: str) -> list[list[list[str]]]:
    """Highlighted `[class suffix, text]` pairs per row; each side tokenized whole."""
    sides: dict[str, list[list[list[str]]]] = {}
    for side, has in (("old", lambda r: r.old), ("new", lambda r: r.new)):
        text = "\n".join(r.text for r in rows if has(r))
        lines = split_lines(tokenize(text, language)) if text else [[]]
        sides[side] = [[[CLASS_OF.get(k, ""), t] for k, t in line] for line in lines]
    out: list[list[list[str]]] = []
    counts = {"old": 0, "new": 0}
    for row in rows:
        use = "new" if row.new else "old"
        counts["old"] += bool(row.old)
        counts["new"] += bool(row.new)
        found = sides[use]
        index = counts[use] - 1
        out.append(found[index] if index < len(found) else [["", row.text]])
    return out


def _block_props(block: Block, codes: dict[int, list[list[str]]]) -> dict[str, object]:
    return {
        "kind": block.kind,
        "header": block.header,
        "rows": _token_rows(block.rows, codes),
    }


def _diff_source(data: dict[str, object]) -> tuple[list[Row], str, str]:
    """Rows, old name and new name of a patch or a before/after pair."""
    patch = data.get("patch")
    if isinstance(patch, str):
        return patch_rows(patch) or ([], "", "")
    return diff_rows(str(data["before"]), str(data["after"])), "", ""


def _copy_text(data: dict[str, object], name: str) -> str:
    patch = data.get("patch")
    if isinstance(patch, str):
        return "\n".join(text_lines(patch))
    return unified_text(str(data["before"]), str(data["after"]), name)


def _note_props(notes: list) -> list[dict[str, object]]:
    return [
        {
            "number": n.number,
            "side": n.side,
            "start": n.start,
            "where": n.where,
            "text": n.text,
        }
        for n in notes
    ]


def diff_props(data: dict[str, object]) -> dict[str, object]:
    """What the `diff` component draws: highlighted rows in blocks, notes and header."""
    rows, old_name, new_name = _diff_source(data)
    name = str(data.get("filename") or new_name or old_name or "diff")
    copy = _copy_text(data, name)
    language = str(data.get("language", ""))
    notes = read_notes(data)
    uid = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:8]
    shown = rows[:MAX_ROWS]
    codes = dict(zip(map(id, shown), _row_tokens(shown, language), strict=True))
    last = max([r.new or r.old or 0 for r in rows] + [1])
    return {
        "name": name,
        "language": language,
        "uid": uid,
        "digits": min(len(str(last)), MAX_DIGIT_CLASS),
        "split": data.get("mode") == "split",
        "change": change_word(rows, old_name, new_name),
        "was": old_name,
        "count": _count_text(rows),
        "copy": copy,
        "blocks": [_block_props(b, codes) for b in layout(rows, anchored(notes))],
        "notes": _note_props(notes),
    }
