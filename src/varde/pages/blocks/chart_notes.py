"""Chart notes: point markers and bands, with tone.

`NOTE_PROPERTIES` is the shape `chart` declares for `notes`; `note_rule_faults`
checks what the metadata cannot express.
"""

import math

from varde.pages.blocks.rules import Fault, is_number, tables
from varde.pages.blocks.spec import PropertySpec

MAX_NOTES = 12
TONES = ("info", "decision", "risk", "warning", "success")
# x, from and to take a label or a number; `_point_fault` checks the value.
NOTE_PROPERTIES = (
    PropertySpec("label", "string", required=True, nonempty=True),
    PropertySpec("tone", "string", enum=TONES),
    PropertySpec("x", "any"),
    PropertySpec("from", "any"),
    PropertySpec("to", "any"),
)


def _finite(value: object) -> bool:
    return is_number(value) and math.isfinite(value)  # type: ignore[arg-type]


def _point_fault(data: dict[str, object], value: object, where: str) -> Fault | None:
    labels = data.get("labels")
    if data.get("kind") == "scatter":
        ok = _finite(value)
        return None if ok else Fault("note-x", f"{where} must be a number")
    ok = isinstance(labels, list) and isinstance(value, str) and value in labels
    return None if ok else Fault("note-x", f"{where} must be one of the labels")


def _scatter_span(data: dict[str, object]) -> tuple[float, float] | None:
    xs = [
        x
        for s in tables(data, "series", "chart")
        for x in (s.get("x") if isinstance(s.get("x"), list) else [])  # type: ignore[union-attr]
        if _finite(x)
    ]
    return (min(xs), max(xs)) if xs else None  # type: ignore[type-var]


def _scatter_range_faults(
    data: dict[str, object], start: object, end: object, where: str
) -> list[Fault]:
    if not (_finite(start) and _finite(end)):
        return []
    if start >= end:  # type: ignore[operator]
        return [Fault("note-range", f"{where}: from must be less than to")]
    span = _scatter_span(data)
    if span and not (span[0] <= start and end <= span[1]):  # type: ignore[operator]
        return [Fault("note-range", f"{where}: from and to must lie in the data")]
    return []


def _range_faults(
    data: dict[str, object], note: dict[str, object], where: str
) -> list[Fault]:
    start, end = note["from"], note["to"]
    if data.get("kind") == "scatter":
        return _scatter_range_faults(data, start, end, where)
    labels = data.get("labels")
    if not isinstance(labels, list) or start not in labels or end not in labels:
        return []
    if labels.index(start) > labels.index(end):
        return [Fault("note-range", f"{where}: from must not come after to")]
    return []


def _marker_faults(
    data: dict[str, object], note: dict[str, object], where: str
) -> list[Fault]:
    fault = _point_fault(data, note["x"], f"{where}.x")
    return [fault] if fault else []


def _band_faults(
    data: dict[str, object], note: dict[str, object], where: str
) -> list[Fault]:
    faults = [
        Fault("missing-key", f"{where}: missing required key '{key}'")
        for key in ("from", "to")
        if key not in note
    ]
    ends = [
        (key, _point_fault(data, note[key], f"{where}.{key}"))
        for key in ("from", "to")
        if key in note
    ]
    faults += [fault for _, fault in ends if fault]
    if len(ends) == 2 and not any(fault for _, fault in ends):
        faults += _range_faults(data, note, where)
    return faults


def _note_rule_faults(
    data: dict[str, object], note: dict[str, object], where: str
) -> list[Fault]:
    if "x" in note and ("from" in note or "to" in note):
        return [Fault("note-mixed", f"{where}: x cannot be combined with from or to")]
    body = _marker_faults if "x" in note else _band_faults
    return body(data, note, where)


def note_rule_faults(data: dict[str, object]) -> list[Fault]:
    """Rules the metadata cannot express: count, marker or band form, positions."""
    faults: list[Fault] = []
    found = tables(data, "notes", "chart")
    if len(found) > MAX_NOTES:
        faults.append(Fault("too-many", f"chart.notes: at most {MAX_NOTES} notes"))
    for n, note in enumerate(found, 1):
        faults += _note_rule_faults(data, note, f"notes[{n}]")
    return faults
