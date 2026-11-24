"""Props for the change-summary component (`static/components/change-summary.js`).

The sentence counts the change markers of the whole page, so the server adds it
as `text`; the component shows it and copies it.
"""

from collections.abc import Iterable

from ..blocks.change_summary import UNCOUNTED, Marker, sentence


def change_summary_props(
    data: dict[str, object], markers: Iterable[Marker] | None = None
) -> dict[str, object]:
    """The block's props plus `text`, the sentence; no marker list is "not scanned"."""
    text = UNCOUNTED if markers is None else sentence(markers)
    title = str(data["title"]) if "title" in data else ""
    return {**data, "text": text, "copy": "\n".join(p for p in (title, text) if p)}
