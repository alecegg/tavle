"""Assemble served pages and their comment threads."""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from varde.pagelib.page.assemble import include_ctx, parse_page_stream, read_markdown
from varde.pagelib.page.render import RenderedPage
from varde.pagelib.page.template import page_shell
from varde.pagelib.page.theme_page import ThemeLayers, no_layers, page_theme
from varde.pages.comments import ANSWER_KINDS, fold, mark_latest_decisions, read_rows


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


@dataclass(frozen=True)
class AssembledPage:
    html: str
    # include id -> confined source path; filled once `include` statements exist
    parts: dict[str, Path] = field(default_factory=dict)


def _served_main(
    doc: Path, theme_layers: ThemeLayers = no_layers
) -> tuple[str, dict[str, Path]]:
    """The served page's `main` element, and the paths of its includes."""
    text = read_markdown(doc)
    ctx, sources = include_ctx(text, doc)
    page = parse_page_stream(text, doc.name, ctx)
    threads = render_threads(page, mark_latest_decisions(fold(read_rows(doc))))
    theme = page_theme(doc, text, theme_layers)
    return (
        f'<main data-role="page">{theme.style}{theme.error}{page.body}{threads}</main>',
        sources,
    )


def assemble(
    doc: Path, *, token: str, api_base: str = "", theme_layers: ThemeLayers = no_layers
) -> AssembledPage:
    main, sources = _served_main(doc, theme_layers)
    return AssembledPage(page_shell(doc.name, main, token, api_base), sources)


def assemble_page(
    doc: Path, *, token: str, api_base: str = "", theme_layers: ThemeLayers = no_layers
) -> str:
    """Full served HTML for `doc`; see `page_shell` for `api_base`."""
    return assemble(doc, token=token, api_base=api_base, theme_layers=theme_layers).html
