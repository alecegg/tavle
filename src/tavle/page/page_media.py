"""Find and probe image references in a Markdown page."""

from pathlib import Path

from ..media import Media, Problem, probe
from .fences import ui_statements


def page_media(
    text: str, doc: Path, *, embed: bool = False
) -> dict[str, Media | Problem]:
    """Probe every distinct, well-formed `src` of the page's image statements."""
    found: dict[str, Media | Problem] = {}
    for _, statement in ui_statements(text):
        src = statement.props.get("src")
        if statement.component == "image" and isinstance(src, str) and src not in found:
            found[src] = probe(src, doc.parent, embed=embed)
    return found
