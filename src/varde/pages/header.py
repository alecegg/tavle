"""Page header strip from frontmatter: status chip, plan, commit, links, reading time.

Pure functions. `header_html` builds the whole `<header class="doc-header">`; a page
with none of the strip keys (`status`, `plan`, `commit`, `links`) keeps the plain
status line. The file name shows only on a page with no H1 of its own.
"""

from __future__ import annotations

import html
import math
import re
from urllib.parse import urlsplit

from varde.pages.blocks_render.common import dated_html
from varde.pages.markdown_syntax import FenceScanner

STRIP_KEYS = ("status", "plan", "commit", "links")
_META_KEYS = ("type", "risk", "status_at")
_WORDS_PER_MINUTE = 200
_MAX_LINKS = 8
_LINK_LABEL = 40
_COMMIT_SHOWN = 9
_PAGE_NAME = re.compile(
    r"^[A-Za-z0-9_][A-Za-z0-9._-]*(/[A-Za-z0-9_][A-Za-z0-9._-]*)*\.md$"
)
_WORD = re.compile(r"[^\W_]", re.UNICODE)

# status word -> (tone, icon); tones are the five ds-tokens triples.
# The icon names a css shape in 65-header.css.
_STATUS: dict[str, tuple[str, str]] = {
    "todo": ("decision", "ring"),
    "backlog": ("decision", "ring"),
    "planned": ("decision", "ring"),
    "draft": ("decision", "ring"),
    "proposed": ("decision", "ring"),
    "in-progress": ("info", "half"),
    "in_progress": ("info", "half"),
    "active": ("info", "half"),
    "building": ("info", "half"),
    "running": ("info", "half"),
    "review": ("warning", "triangle"),
    "in-review": ("warning", "triangle"),
    "pending": ("warning", "triangle"),
    "paused": ("warning", "triangle"),
    "on-hold": ("warning", "triangle"),
    "blocked": ("risk", "cross"),
    "failed": ("risk", "cross"),
    "rejected": ("risk", "cross"),
    "abandoned": ("risk", "cross"),
    "cancelled": ("risk", "cross"),
    "done": ("success", "check"),
    "complete": ("success", "check"),
    "completed": ("success", "check"),
    "approved": ("success", "check"),
    "merged": ("success", "check"),
    "concluded": ("success", "check"),
}
_NEUTRAL = ("neutral", "dot")


def status_tone(status: str) -> tuple[str, str]:
    """Tone name and icon name for a status word; unknown words are neutral."""
    return _STATUS.get(status.strip().lower(), _NEUTRAL)


def count_words(lines: list[str]) -> int:
    """Words of prose and table text; fenced blocks (code and `ui`) are skipped."""
    words = 0
    scanner = FenceScanner("words")
    for line in lines:
        if scanner.feed(line) or scanner.opening:
            continue
        words += sum(1 for token in line.split() if _WORD.search(token))
    return words


def reading_minutes(words: int) -> int:
    return max(1, math.ceil(words / _WORDS_PER_MINUTE))


def parse_links(raw: str) -> list[tuple[str, str]]:
    """(href, label) per safe entry of a comma-separated list; others are dropped."""
    links: list[tuple[str, str]] = []
    for entry in (part.strip() for part in raw.split(",")):
        link = _safe_link(entry)
        if link and link not in links:
            links.append(link)
    return links[:_MAX_LINKS]


def _safe_link(entry: str) -> tuple[str, str] | None:
    if _PAGE_NAME.match(entry):
        return entry, entry
    if not entry.lower().startswith(("http://", "https://")) or re.search(
        r"[\s<>\"'\\]", entry
    ):
        return None
    parts = urlsplit(entry)
    if not parts.hostname:
        return None
    label = parts.netloc + (parts.path if parts.path != "/" else "")
    if len(label) > _LINK_LABEL:
        label = label[: _LINK_LABEL - 1] + "…"
    return entry, label


def header_item(label: str, value: str, title: str = "") -> str:
    shown = f'<span class="vd-hdr-value"{_title(title)}>{dated_html(value)}</span>'
    return (
        f'<li class="vd-hdr-item"><span class="vd-hdr-key">{label}</span> {shown}</li>'
    )


def _title(text: str) -> str:
    return f' title="{html.escape(text, quote=True)}"' if text else ""


def header_chip(status: str) -> str:
    tone, icon = status_tone(status)
    return (
        f'<li class="vd-hdr-chip vd-hdr-{tone}">'
        f'<span class="vd-hdr-glyph vd-hdr-glyph-{icon}" aria-hidden="true"></span>'
        f'<span class="status">{html.escape(status)}</span></li>'
    )


def _links(links: list[tuple[str, str]]) -> str:
    return "".join(
        '<li class="vd-hdr-linkitem"><a class="vd-hdr-link"'
        f' href="{html.escape(href, quote=True)}"'
        f' rel="noopener"{_title(href)}>{html.escape(label)}</a></li>'
        for href, label in links
    )


def strip_html(fields: dict[str, str], doc_name: str, words: int) -> str:
    items = []
    if fields.get("status"):
        items.append(header_chip(fields["status"]))
    items.append(header_item("Plan", fields.get("plan") or doc_name))
    if fields.get("commit"):
        commit = fields["commit"]
        items.append(header_item("Commit", commit[:_COMMIT_SHOWN], commit))
    meta = [f"{key}: {fields[key]}" for key in _META_KEYS if fields.get(key)]
    if meta:
        items.append(
            f'<li class="vd-hdr-item vd-hdr-meta">{dated_html(" · ".join(meta))}</li>'
        )
    items.append(
        f'<li class="vd-hdr-item vd-hdr-time">{reading_minutes(words)} min</li>'
    )
    items.append(_links(parse_links(fields.get("links", ""))))
    return f'<ul class="vd-hdr" aria-label="Page details">{"".join(items)}</ul>'


def plain_status(fields: dict[str, str]) -> str:
    keys = ("type", "status", "risk", "status_at")
    return " · ".join(f"{key}: {fields[key]}" for key in keys if fields.get(key))


def header_html(
    fields: dict[str, str], doc_name: str, words: int, *, titled: bool
) -> str:
    """The page `<header>`: the file name (unless the page has its own H1), then the
    strip (or today's plain status line). Empty when none of them has content."""
    parts = [] if titled else [f'<p class="doc-name">{html.escape(doc_name)}</p>']
    if any(fields.get(key) for key in STRIP_KEYS):
        parts.append(strip_html(fields, doc_name, words))
    elif plain_status(fields):
        parts.append(f'<p class="status">{html.escape(plain_status(fields))}</p>')
    if not parts:
        return ""
    return f'<header class="doc-header">{"".join(parts)}</header>'
