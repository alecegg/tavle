"""The shared change vocabulary: which rows changed, and the text that says so.

Pure functions. The browser draws the glyph and the word (`static/components/shared.js`
`changeBadge`); this module decides the change of a validated item and writes the
Copy text and legend line. Status is never colour alone: the glyph and the word
are text.
"""

from collections.abc import Mapping, Sequence

GLYPHS = {"added": "+", "modified": "~", "removed": "-", "renamed": "->"}


def change_of(item: Mapping[str, object]) -> tuple[str, str]:
    """The `(change, was)` pair of a validated table; empty strings when absent."""
    return str(item.get("change", "")), str(item.get("was", ""))


def field_props(name: str, value: object, key: object) -> dict[str, object]:
    """A field or parameter for the browser: type, change and whether it is the key."""
    if isinstance(value, Mapping):
        kind, (change, was) = str(value["type"]), change_of(value)
    else:
        kind, change, was = str(value), "", ""
    return {
        "name": name,
        "type": kind,
        "change": change,
        "was": was,
        "key": name == key,
    }


def copy_line(change: str, name: str, was: str) -> str:
    """`<change> <name> (was <was>)` for the Copy entry of the action menu."""
    return f"{change} {name} (was {was})" if was else f"{change} {name}"


def legend_text(changes: Sequence[str]) -> str:
    """The text alternative: how many rows carry each change."""
    counts = [f"{changes.count(c)} {c}" for c in GLYPHS if c in changes]
    return f"Changes: {', '.join(counts)}"
