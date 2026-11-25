"""Hard precondition: a cell audits rendered components, not a code block.

A page that shows `ui` fences as plain code has no widgets to fail, so every
audit would pass vacuously. `NotRendered` is not an AssertionError, so a
pending-family `xfail(raises=AssertionError)` cannot hide it.
"""

from __future__ import annotations

import re
from typing import Any

from tavle.blocks_render import COMPONENTS

STATEMENT = re.compile(r"^[A-Za-z][\w-]*\s*=\s*([a-z][\w-]*)\(", re.MULTILINE)
ROOTS_JS = r"""() => ({
  roots: [...document.querySelectorAll('.vb')].map((n) => [...n.classList]),
  fallbacks: document.querySelectorAll('pre.vd-noscript').length,
  code: [...document.querySelectorAll('pre:not(.vd-noscript)')].map((n) => (n.textContent || '').slice(0, 4000)),
})"""


class NotRendered(Exception):
    """The page shows component source instead of rendered components."""


def components_in(text: str) -> list[str]:
    """Component names of every `ui` statement in a fixture, includes excluded."""
    names = STATEMENT.findall(text)
    return [n for n in names if n != "include"]


def not_rendered(text: str, page: dict[str, Any], *, nojs: bool = False) -> list[str]:
    """Reasons the page lacks the fixture's components (empty when rendered).

    With JavaScript off, a client-rendered block shows its Markdown source in a
    `pre.vd-noscript`, so each one needs that fallback instead of a `.vb` root.
    A refused block (an image whose file is unusable) is an error card with a bare
    `.vb` root on the server, so it stands in for one fallback.
    """
    names = components_in(text)
    problems: list[str] = []
    if nojs:
        client = [n for n in names if n in COMPONENTS]
        refused = sum(classes == ["vb"] for classes in page["roots"])
        if page["fallbacks"] + refused < len(client):
            problems.append(
                f"{page['fallbacks']} noscript sources for {len(client)} client blocks"
            )
        names = [n for n in names if n not in client]
    roots: list[list[str]] = page["roots"]
    problems += [
        f"no .vb.{n} element for the '{n}' statement"
        for n in sorted(set(names))
        if not any(n in classes for classes in roots)
    ]
    if len(roots) < len(names):
        problems.append(f"{len(roots)} .vb roots for {len(names)} component statements")
    problems += [
        "a <pre> block shows a component statement as code"
        for code in page["code"]
        if STATEMENT.search(code)
    ][:1]
    return problems


# ruff: noqa: E501
