"""Assemble one served or exported page: parse, render, wrap in the host shell."""

from __future__ import annotations

from pathlib import Path

from varde.pagelib.page.include import (
    IncludeError,
    find_includes,
    resolve_includes,
)
from varde.pagelib.page.markdown_syntax import FenceScanner
from varde.pagelib.page.page_media import page_media
from varde.pagelib.page.render import (
    PageCtx,
    RenderedPage,
    render_page,
    strip_comments,
)
from varde.pagelib.page.template import page_css
from varde.pagelib.page.theme_page import ThemeLayers, no_layers, require_theme
from varde.ui import export_page, make_read_only, parse_lines


def read_markdown(doc: Path) -> str:
    try:
        return doc.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return f"# Unreadable\n\n{doc.name} could not be read."


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def drop_pending_tail(text: str) -> str:
    """Cut a half-written trailing `ui` fence back to its complete statements.

    Complete text is returned unchanged; a cut text is normalised to the
    renderer's own line view (tabs expanded, comments stripped, `\\n` ends).
    """
    lines = strip_comments(text.expandtabs(4).splitlines())
    scanner = FenceScanner()
    for i, line in enumerate(lines):
        scanner.feed(line, i)
    opening = scanner.opening
    if opening is None or opening.group(3) != "ui":
        return text
    at = scanner.start
    indent = len(opening.group(1))
    body = [
        line[min(indent, len(line) - len(line.lstrip())) :] for line in lines[at + 1 :]
    ]
    pending = parse_lines("\n".join(body), partial=True).pending
    if not pending:
        return text
    kept = "\n".join(body)[: -len(pending)]
    kept_lines = lines[at + 1 : at + 1 + kept.count("\n")]
    return "\n".join([*lines[: at + 1], *kept_lines, opening.group(2)]) + "\n"


def parse_page_stream(
    text: str, doc_name: str, ctx: PageCtx | None = None
) -> RenderedPage:
    """Parse a half-written page: an unfinished `ui` statement renders as nothing."""
    return render_page(drop_pending_tail(text), doc_name, ctx)


def include_ctx(
    text: str, doc: Path, *, export: bool = False
) -> tuple[PageCtx, dict[str, Path]]:
    """The render context holding each include's part HTML, and its source paths.

    It also holds the page's image files (inlined when `export`).
    """
    whole = drop_pending_tail(text)
    media = page_media(whole, doc, embed=export)
    try:
        parts = resolve_includes(whole, doc.parent) if find_includes(whole) else {}
    except IncludeError as error:
        return PageCtx(
            doc.name, include_error=str(error), media=media, export=export
        ), {}
    shown = {name: part.html for name, part in parts.items()}
    ctx = PageCtx(doc.name, shown, media=media, export=export)
    return ctx, {name: part.source.path for name, part in parts.items()}


def assemble_static(doc: Path, theme_layers: ThemeLayers = no_layers) -> str:
    """Self-contained export: no token or comments; inputs read-only.

    The only script is the component bundle, inlined when a block needs it.
    """
    text = read_markdown(doc)
    page = render_page(text, doc.name, include_ctx(text, doc, export=True)[0])
    style = require_theme(doc, text, theme_layers)
    main = f'<main data-role="page">{style}{make_read_only(page.body)}</main>'
    return export_page(doc.name, main, page_css())
