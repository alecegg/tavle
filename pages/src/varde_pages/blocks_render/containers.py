"""tabs and columns: panel props for the browser, and filling the held blocks in.

A container renders as a host (`static/components/tabs.js`, `columns.js`) that names
each panel's held block ids. `fill_containers` is page assembly, not drawing: given
the page's wrapped statement blocks, it returns each container's host with the held
blocks as `<div class="vd-containers-slot" data-hold="id">` children, so a held
block is rendered once and keeps its own id, host and action menu. Mounting lifts
those children out and each panel slot adopts them. Every panel shows by default
(headings label them); `containers.js` turns tab panels into a tablist. Which ids a
container may hold is decided by `blocks.containers.held_faults`.
"""

import hashlib
import html
import re
from collections.abc import Mapping
from dataclasses import dataclass

from varde_pages.blocks.check import INPUT_COMPONENTS, check_props
from varde_pages.blocks.containers import CONTAINERS, HOLD_KEYS, Statements, held_faults
from varde_pages.blocks_render.common import as_dict, as_list, esc
from varde_pages.components import mount_block

_COPY = re.compile(r' data-copy="([^"]*)"')
_TAG = re.compile(r"<[^>]*>")


@dataclass(frozen=True)
class Placed:
    """A statement's block as the page wraps it, which a container may hold."""

    component: str
    props: Mapping[str, object]
    source: str
    digest: str
    html: str  # the wrapped block


@dataclass(frozen=True)
class Filled:
    """A container's host with its held blocks inside, and its new hash."""

    host: str
    digest: str


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


def _copy_of(block: str) -> str:
    marked = _COPY.search(block)
    if marked:
        return html.unescape(marked.group(1))
    return " ".join(html.unescape(_TAG.sub(" ", block)).split())


def _note(text: str) -> str:
    return f'<p class="vd-containers-note">{esc(text)}</p>'


def _refusal_note(rule: str, own: str, held: str) -> str:
    """The note a refused held id shows in its slot."""
    if rule == "container-input":
        return f"Input '{held}' cannot be held in tabs."
    if rule in {"container-nested", "container-cycle"} and held != own:
        return f"Block '{held}' is a container; containers do not nest."
    return f"Block '{held}' is missing, held elsewhere, or is this container."


def _slot(held: str, content: str) -> str:
    return f'<div class="vd-containers-slot" data-hold="{esc(held)}">{content}</div>'


def _fill_one(
    ident: str,
    block: Placed,
    placed: Mapping[str, Placed],
    refused: Mapping[tuple[str, str], str],
    taken: set[str],
) -> Filled:
    shown = container_props(block.component, dict(block.props))
    slots: list[str] = []
    copies: list[str] = []
    hashes: list[str] = []
    for panel in as_list(shown["panels"]):
        label = panel["label"]
        copies += [label] if label else []
        for held in panel["blocks"]:
            rule = refused.get((ident, held))
            if rule == "container-double" and held not in taken:
                rule = None  # the earlier holder was itself refused
            if rule or held not in placed or held in taken:
                note = _refusal_note(rule or "container-unknown", ident, held)
                slots.append(_slot(held, _note(note)))
                continue
            taken.add(held)
            slots.append(_slot(held, placed[held].html))
            copy = _copy_of(placed[held].html)
            copies += [copy] if copy else []
            hashes.append(placed[held].digest)
    host = mount_block(
        block.component,
        shown,
        block.source,
        ident,
        "\n\n".join(copies),
        "".join(slots),
    )
    return Filled(host, _held_digest(block.digest, hashes))


def _held_digest(own: str, hashes: list[str]) -> str:
    """The container's hash, changed by its held blocks' hashes."""
    if not hashes:
        return own
    return hashlib.sha256((own + "".join(hashes)).encode()).hexdigest()[:12]


def fill_containers(
    statements: Statements, placed: Mapping[str, Placed]
) -> tuple[dict[str, Filled], set[str]]:
    """Each container's filled host by id, and the ids of the blocks moved into them.

    `statements` is every statement of the page; `placed` holds those drawn as blocks,
    by id, in page order. A container whose props are invalid is an error card: it
    holds nothing.
    """
    invalid = {
        ident
        for ident, block in placed.items()
        if block.component in CONTAINERS
        and check_props(block.component, dict(block.props), 0)
    }
    # An invalid container is an error card: it holds nothing and may be held.
    refused = {
        (own, held): fault.rule
        for _, own, held, fault in held_faults(
            [s for s in statements if s[2] not in invalid], INPUT_COMPONENTS
        )
        if fault.rule != "container-unknown"  # `placed` decides what is missing
    }
    taken: set[str] = set()
    filled: dict[str, Filled] = {}
    for ident, block in placed.items():
        if block.component in CONTAINERS and ident not in invalid:
            filled[ident] = _fill_one(ident, block, placed, refused, taken)
    return filled, taken
