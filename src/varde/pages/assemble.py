"""Assemble one served or exported page: parse, render, wrap in the host shell."""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from varde.pages.comments import (
    ANSWER_KINDS,
    fold,
    mark_latest_decisions,
    read_rows,
)
from varde.pages.components import export_page
from varde.pages.include import (
    IncludeError,
    find_includes,
    resolve_includes,
)
from varde.pages.markdown_syntax import FenceScanner
from varde.pages.page_media import page_media
from varde.pages.render import (
    PageCtx,
    RenderedPage,
    render_page,
    strip_comments,
)
from varde.pages.template import make_read_only, page_shell
from varde.pages.theme.page import page_theme, require_theme
from varde.ui.lines import parse_lines


def answer_attrs(comment: dict[str, Any]) -> str:
    """Item, value and `latest` of an answer row, for showing the stored verdict."""
    if comment.get("kind") not in ANSWER_KINDS or not isinstance(
        comment.get("item"), str
    ):
        return ""
    value = comment.get("value", comment.get("verdict", ""))
    latest = "true" if comment.get("latest") else "false"
    return (
        f' data-item="{html.escape(comment["item"])}"'
        f' data-value="{html.escape(str(value))}" data-latest="{latest}"'
    )


def render_thread(comment: dict[str, Any], orphan: bool) -> str:
    def esc(value: object) -> str:
        return html.escape(str(value))

    classes = "thread" + (" orphan" if orphan else "")
    if comment.get("state") == "resolved":
        classes += " resolved"

    def meta(row: dict[str, Any]) -> str:
        return (
            f'<p class="meta">{esc(row.get("actor", ""))} {esc(row.get("ts", ""))}</p>'
        )

    def text(row: dict[str, Any]) -> str:
        return f'<p class="text">{esc(row.get("text", ""))}</p>'

    anchor = esc(comment.get("anchor", ""))
    kind = esc(comment.get("kind", "comment"))
    cid = esc(comment.get("id", ""))
    open_tag = (
        f'<article class="{classes}" data-anchor="{anchor}" '
        f'data-id="{cid}" data-kind="{kind}"{answer_attrs(comment)}>'
    )
    parts = [open_tag]
    if orphan and comment.get("quote"):
        parts.append(f"<blockquote>{esc(comment['quote'])}</blockquote>")
    parts += [meta(comment), text(comment)]
    if comment.get("kind") == "suggestion":
        parts.append(
            f'<p class="suggestion"><del>{esc(comment.get("quote", ""))}</del> '
            f"<ins>{esc(comment.get('replacement', ''))}</ins></p>"
        )
        if comment.get("applied_by"):
            parts.append(f'<p class="meta">applied by {esc(comment["applied_by"])}</p>')
    parts += [
        f'<div class="reply">{meta(r)}{text(r)}</div>'
        for r in comment.get("replies", [])
    ]
    parts.append("</article>")
    return "".join(parts)


def render_threads(page: RenderedPage, comments: list[dict[str, Any]]) -> str:
    anchors = {block.anchor for block in page.blocks}
    placed = [c for c in comments if c.get("anchor") in anchors]
    orphans = [c for c in comments if c.get("anchor") not in anchors]
    out = [render_thread(c, orphan=False) for c in placed]
    if orphans:
        out.append('<section class="orphans"><h2>Comments on edited text</h2>')
        out.extend(render_thread(c, orphan=True) for c in orphans)
        out.append("</section>")
    return "".join(out)


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


@dataclass(frozen=True)
class AssembledPage:
    html: str
    # include id -> confined source path; filled once `include` statements exist
    parts: dict[str, Path] = field(default_factory=dict)


def _served_main(doc: Path) -> tuple[str, dict[str, Path]]:
    """The served page's `main` element, and the paths of its includes."""
    text = read_markdown(doc)
    ctx, sources = include_ctx(text, doc)
    page = parse_page_stream(text, doc.name, ctx)
    threads = render_threads(page, mark_latest_decisions(fold(read_rows(doc))))
    theme = page_theme(doc, text)
    return (
        f'<main data-role="page">{theme.style}{theme.error}{page.body}{threads}</main>',
        sources,
    )


def assemble(doc: Path, *, token: str, api_base: str = "") -> AssembledPage:
    main, sources = _served_main(doc)
    return AssembledPage(page_shell(doc.name, main, token, api_base), sources)


def assemble_page(doc: Path, *, token: str, api_base: str = "") -> str:
    """Full served HTML for `doc`; see `page_shell` for `api_base`."""
    return assemble(doc, token=token, api_base=api_base).html


def assemble_static(doc: Path) -> str:
    """Self-contained export: no token or comments; inputs read-only.

    The only script is the component bundle, inlined when a block needs it.
    """
    text = read_markdown(doc)
    page = render_page(text, doc.name, include_ctx(text, doc, export=True)[0])
    style = require_theme(doc, text)
    main = f'<main data-role="page">{style}{make_read_only(page.body)}</main>'
    return export_page(doc.name, main)
