"""tabs and columns: panel props for the browser, and filling the held blocks in.

A container renders as a host (`static/components/tabs.js`, `columns.js`) that names
each panel's held block ids. `fill_containers` is page assembly, not drawing: it
moves the already-rendered held blocks into the container's host as
`<div class="vd-containers-slot" data-hold="id">` children, so a held block is
rendered once and keeps its own id, host and action menu. Mounting lifts those
children out and each panel slot adopts them. Every panel shows by default (headings
label them); `containers.js` turns tab panels into a tablist.
"""

import hashlib
import html
import re

from varde_pages.blocks.containers import HOLD_KEYS
from varde_pages.blocks.spec import INPUT_BLOCK_TYPES
from varde_pages.blocks_render.common import as_dict, as_list, esc
from varde_pages.components import host_props

_ROOT = re.compile(
    r'<div class="block" id="blk-([a-z0-9-]+)" data-anchor="[^"]*" '
    r'data-hash="([0-9a-f]+)" data-block-type="visual">'
    r'<div data-mithril="(tabs|columns)" data-block-id="[^"]*" data-copy="">'
)
_CONTAINER_HEAD = re.compile(
    r'^<div class="block"[^>]*><div data-mithril="(tabs|columns)"'
)
_HOST_TAIL = "</div></div>"  # the host and its block wrapper close the root
_DIV = re.compile(r"<div\b|</div>")
_COPY = re.compile(r' data-copy="([^"]*)"')
_TAG = re.compile(r"<[^>]*>")
_HASH = re.compile(r'data-hash="([0-9a-f]+)"')
_SENTINEL = "\x00container\x00"


def container_props(kind: str, props: dict[str, object]) -> dict[str, object]:
    """Panels for the browser; `fill_containers` fills `copy` from held blocks."""
    panels = [as_dict(p) for p in as_list(props.get(HOLD_KEYS[kind]))]
    return {
        "panels": [
            {"label": str(p.get("label") or ""), "blocks": as_list(p.get("blocks"))}
            for p in panels
        ],
        "copy": "",
    }


# --- filling ----------------------------------------------------------------


def _block_start(body: str, ident: str) -> int:
    return body.find(f'<div class="block" id="blk-{ident}" ')


def _block_end(body: str, start: int) -> int:
    """Index after the `</div>` closing the block that opens at `start`."""
    depth = 0
    for tag in _DIV.finditer(body, start):
        depth += 1 if tag.group().startswith("<div") else -1
        if depth == 0:
            return tag.end()
    return len(body)


def _copy_of(block: str) -> str:
    marked = _COPY.search(block)
    if marked:
        return html.unescape(marked.group(1))
    return " ".join(html.unescape(_TAG.sub(" ", block)).split())


def _note(text: str) -> str:
    return f'<p class="vd-containers-note">{esc(text)}</p>'


def _take(body: str, held: str, kind: str, taken: set[str]) -> tuple[str, str, str]:
    """(body without the held block, its HTML or a note, its copy text)."""
    start = _block_start(body, held)
    if start >= 0 and held in taken:
        start = -1
    if start < 0:
        return (
            body,
            _note(f"Block '{held}' is missing, held elsewhere, or is this container."),
            "",
        )
    end = _block_end(body, start)
    block = body[start:end]
    if _CONTAINER_HEAD.match(block):
        return (
            body,
            _note(f"Block '{held}' is a container; containers do not nest."),
            "",
        )
    if kind == "tabs" and any(
        f'data-block-type="{t}"' in block[:300] for t in INPUT_BLOCK_TYPES
    ):
        return body, _note(f"Input '{held}' cannot be held in tabs."), ""
    taken.add(held)
    return body[:start] + body[end:], block, _copy_of(block)


def _fill_root(
    body: str, root: str, kind: str, taken: set[str]
) -> tuple[str, str, str, list[str]]:
    """(body, filled HTML, copy text, held hashes) with the held blocks moved in."""
    panels = as_list(host_props(root, kind)[0]["panels"])
    slots: list[str] = []
    copies: list[str] = []
    hashes: list[str] = []
    for panel in panels:
        label = panel["label"]
        copies += [label] if label else []
        for held in panel["blocks"]:
            body, block, copy = _take(body, held, kind, taken)
            slots.append(
                f'<div class="vd-containers-slot" data-hold="{esc(held)}">{block}</div>'
            )
            copies += [copy] if copy else []
            hashes += _HASH.findall(block[:300])
    filled = root.removesuffix(_HOST_TAIL) + "".join(slots) + _HOST_TAIL
    return body, filled, "\n\n".join(copies), hashes


def _stamp(filled: str, copy: str, hashes: list[str]) -> str:
    """Give the container the copy text and a hash that changes with its held blocks."""
    filled = filled.replace(' data-copy=""', f' data-copy="{esc(copy)}"', 1)
    own = _HASH.search(filled)
    if own is None or not hashes:
        return filled
    digest = hashlib.sha256((own.group(1) + "".join(hashes)).encode()).hexdigest()[:12]
    return filled.replace(own.group(0), f'data-hash="{digest}"', 1)


def _fill_one(body: str, ident: str, kind: str, taken: set[str]) -> str:
    start = _block_start(body, ident)
    end = _block_end(body, start)
    root = body[start:end]
    body = body[:start] + _SENTINEL + body[end:]
    body, filled, copy, hashes = _fill_root(body, root, kind, taken)
    return body.replace(_SENTINEL, _stamp(filled, copy, hashes), 1)


def fill_containers(body: str) -> str:
    """Move each container's held blocks into its host (hash and copy included)."""
    taken: set[str] = set()
    for found in list(_ROOT.finditer(body)):
        body = _fill_one(body, found.group(1), found.group(3), taken)
    return body
