"""Props for annotated-code (`static/components/annotated-code.js`): numbered notes
anchored to line ranges, and the runs of quiet lines the component folds."""

import hashlib
import json
from dataclasses import dataclass

from ..blocks.annotated_code import (
    parse_range,
    source_line_count,
)
from ..blocks_render.code import Panel, code_props

CONTEXT = 3  # unannotated lines kept on each side of a note
MIN_FOLD = 4  # shortest quiet stretch worth a "lines hidden" row
KINDS = {
    "info": ("i", "Info", "info"),
    "warn": ("!", "Warning", "warning"),
    "change": ("Δ", "Change", "decision"),
}


@dataclass(frozen=True)
class Note:
    number: int
    start: int
    end: int
    label: str
    text: str
    kind: str

    @property
    def span_text(self) -> str:
        return (
            f"line {self.start}"
            if self.start == self.end
            else f"lines {self.start}-{self.end}"
        )


def read_notes(data: dict[str, object], total: int) -> list[Note]:
    """Notes numbered by start line (ties keep the author's order), ranges clamped."""
    found: list[tuple[int, int, int, dict[str, object]]] = []
    for index, raw in enumerate(data.get("notes") or []):  # type: ignore[attr-defined]
        span = parse_range(raw.get("lines"))
        if span is None:
            continue
        start = min(span[0], total)
        found.append((start, min(max(span[1], start), total), index, raw))
    found.sort(key=lambda item: (item[0], item[2]))
    return [
        Note(
            n,
            start,
            end,
            str(raw.get("label", "")),
            str(raw["note"]),
            str(raw.get("kind", "info")),
        )
        for n, (start, end, _, raw) in enumerate(found, 1)
    ]


def hidden_runs(notes: list[Note], total: int) -> list[tuple[int, int]]:
    """Runs of lines more than CONTEXT from any note, at least MIN_FOLD long."""
    kept: set[int] = set()
    for note in notes:
        kept.update(
            range(max(note.start - CONTEXT, 1), min(note.end + CONTEXT, total) + 1)
        )
    runs: list[tuple[int, int]] = []
    start = 0
    for line in range(1, total + 2):
        quiet = line <= total and line not in kept
        if quiet and not start:
            start = line
        if not quiet and start:
            runs.append((start, line - 1))
            start = 0
    return [(a, b) for a, b in runs if b - a + 1 >= MIN_FOLD]


def copy_text(source: str, notes: list[Note]) -> str:
    """The source, then the numbered notes."""
    listed = [
        f"{n.number}. {n.span_text}: " + (f"{n.label}: " if n.label else "") + n.text
        for n in notes
    ]
    return "\n\n".join(
        part for part in (source.rstrip("\n"), "\n".join(listed)) if part
    )


def annotated_props(data: dict[str, object]) -> dict[str, object]:
    """What the `annotated-code` component draws: code props, notes and folds."""
    source = str(data["source"])
    total = source_line_count(source)
    notes = read_notes(data, total)
    uid = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:8]
    panel = Panel(
        title=str(data["filename"]), wrap=True, mark=[[n.start, n.end] for n in notes]
    )
    folds = hidden_runs(notes, total) if data.get("collapse") is not False else []
    crowd = (sum(1 for m in notes if m.start == n.start) for n in notes)
    return {
        **code_props(source, str(data["language"]), panel),
        "uid": uid,
        "columns": min(max(crowd, default=1), 6),
        "folds": [list(run) for run in folds],
        "copy": copy_text(source, notes),
        "notes": [_note_props(n) for n in notes],
    }


def _note_props(note: Note) -> dict[str, object]:
    glyph, word, tone = KINDS[note.kind]
    return {
        "number": note.number,
        "start": note.start,
        "end": note.end,
        "label": note.label,
        "text": note.text,
        "kind": note.kind,
        "glyph": glyph,
        "word": word,
        "tone": tone,
        "where": note.span_text,
    }
