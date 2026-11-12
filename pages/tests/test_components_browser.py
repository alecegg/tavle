"""Chromium checks of client-side blocks on a served page (slow tier)."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from varde_pages.serve import PageServer

pytestmark = pytest.mark.slow

CALLOUT = (
    '```ui\nn = callout(tone: "{tone}", title: "T{tone}", text: "Body `x`")\n```\n'
)
DOC = "# Page\n\nLead.\n\n" + CALLOUT.format(tone="decision")


@pytest.fixture(scope="module")
def shared_page(browser_session: Any) -> Any:
    page = browser_session.new_page(viewport={"width": 390, "height": 844})
    page.set_default_timeout(10_000)
    return page


@pytest.fixture
def served(tmp_path: Path, shared_page: Any) -> Iterator[tuple[Any, Path]]:
    doc = tmp_path / "page.md"
    doc.write_text(DOC, encoding="utf-8")
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    page = shared_page
    page.goto(f"http://127.0.0.1:{server.port}/")
    yield page, doc
    page.goto("about:blank")
    server.shutdown()
    server.server_close()
    thread.join(5)


def test_served_callout_is_mounted_and_styled(served: tuple[Any, Path]) -> None:
    page, _ = served
    aside = page.locator("aside.vd-callout-decision")
    aside.wait_for()
    assert (
        "DECISION" in aside.inner_text() and aside.locator("code").inner_text() == "x"
    )
    assert (
        page.evaluate(
            "getComputedStyle(document.querySelector('aside.vd-callout')).borderTopWidth"
        )
        == "1px"
    )
    assert page.locator("[data-mithril] script, [data-mithril] noscript").count() == 0


def test_callout_added_by_a_live_update_is_mounted(served: tuple[Any, Path]) -> None:
    page, doc = served
    page.locator("aside.vd-callout").wait_for()
    doc.write_text(DOC + "\n" + CALLOUT.format(tone="risk"), encoding="utf-8")
    page.locator("aside.vd-callout-risk").wait_for()
    assert page.locator("aside.vd-callout").count() == 2


def tabs_doc(first: str, second: str) -> str:
    def note(ident: str, text: str) -> str:
        call = f'{ident} = callout(tone: "info", text: "{text}")'
        return f"```ui id={ident}\n{call}\n```\n\n"

    panels = '{"label": "One", "blocks": ["a"]}, {"label": "Two", "blocks": ["b"]}'
    return (
        "# Page\n\n"
        + note("a", first)
        + note("b", second)
        + f"```ui id=t\nt = tabs(tab: [{panels}])\n```\n"
    )


@pytest.fixture
def served_tabs(tmp_path: Path, shared_page: Any) -> Iterator[tuple[Any, Path]]:
    doc = tmp_path / "page.md"
    doc.write_text(tabs_doc("First text", "Second text"), encoding="utf-8")
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    shared_page.goto(f"http://127.0.0.1:{server.port}/")
    yield shared_page, doc
    shared_page.goto("about:blank")
    server.shutdown()
    server.server_close()
    thread.join(5)


def test_held_blocks_mount_inside_the_drawn_tabs(served_tabs: tuple[Any, Path]) -> None:
    page, _ = served_tabs
    page.locator(".vd-ctabs-on").wait_for()
    held = page.locator("#blk-t .vd-containers-slot aside.vd-callout")
    assert held.count() == 2
    assert page.locator("#blk-t .vd-ctabs-tab").count() == 2
    assert page.locator("#blk-a:visible").count() == 1  # first tab shows its block
    assert page.locator("#blk-b:visible").count() == 0
    page.locator("#blk-t .vd-ctabs-tab").nth(1).click()
    assert page.locator("#blk-b:visible").count() == 1


def test_a_held_block_changed_by_a_live_update_stays_in_its_tab(
    served_tabs: tuple[Any, Path],
) -> None:
    page, doc = served_tabs
    page.locator(".vd-ctabs-on").wait_for()
    doc.write_text(tabs_doc("First changed", "Second text"), encoding="utf-8")
    page.locator("#blk-t aside.vd-callout", has_text="First changed").wait_for()
    assert page.locator("#blk-t .vd-ctabs-tab").count() == 2
    assert page.locator("#blk-t [role=tablist]").count() == 1
    assert page.locator("#blk-a").count() == 1  # held once, not also on the page
    copy = page.locator('#blk-t [data-mithril="tabs"]').get_attribute("data-copy")
    assert copy is not None and "First changed" in copy
