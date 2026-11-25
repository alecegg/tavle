"""Collapsible sections in served and standalone pages."""

import threading
from pathlib import Path

import pytest
from browser_args import BROWSER_ARGS
from playwright.sync_api import sync_playwright

from tavle import PageServer
from tavle.page.assemble import assemble_static, render_fragment
from tavle.page.render import main_open, render_page

pytestmark = pytest.mark.slow


def test_section_opt_in_and_export(tmp_path):
    doc = tmp_path / "page.md"
    doc.write_text("---\nsections: collapsible\n---\n# Title\n\n## Section\n\nText\n")
    assert 'data-sections="collapsible"' in render_fragment(doc)
    exported = assemble_static(doc)
    assert 'data-sections="collapsible"' in exported
    assert "data-section-toggle" in exported
    assert main_open(render_page("# Title", "page.md")) == '<main data-role="page">'
    assert (
        main_open(render_page("---\nsections: other\n---\n# Title", "page.md"))
        == '<main data-role="page">'
    )


def _long_page(front: str) -> str:
    filler = "\n\n".join(f"Paragraph {n} of the first section." for n in range(60))
    return (
        f"{front}# Board\n\n## First\n\n{filler}\n\n## Second\n\nSecond text.\n\n"
        "# Next part\n\nPart text.\n"
    )


def _served(doc, check) -> None:
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=BROWSER_ARGS)
            try:
                page = browser.new_page(viewport={"width": 1024, "height": 700})
                page.route("**/events", lambda route: route.abort())
                page.goto(f"http://127.0.0.1:{server.port}/")
                page.locator("main .block").first.wait_for()
                check(page)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()


def test_collapse_a_section_and_print(tmp_path: Path) -> None:
    doc = tmp_path / "board.md"
    doc.write_text(_long_page("---\nsections: collapsible\n---\n"))

    def check(page) -> None:
        first = page.locator("#h-first button[data-section-toggle]")
        first.wait_for()
        body = page.get_by_text("Paragraph 3 of the first section.")
        assert first.get_attribute("aria-expanded") == "true"
        first.click()
        assert first.get_attribute("aria-expanded") == "false"
        assert body.is_hidden()
        assert page.locator("#h-second").is_visible()
        assert page.get_by_text("Part text.").is_visible()
        page.evaluate("dispatchEvent(new Event('beforeprint'))")
        assert body.is_visible()
        page.evaluate("dispatchEvent(new Event('afterprint'))")
        assert body.is_hidden()
        page.reload()
        page.locator("#h-first button[aria-expanded='false']").wait_for()
        assert page.get_by_text("Paragraph 3 of the first section.").is_hidden()

    _served(doc, check)


def test_sticky_heading(tmp_path: Path) -> None:
    doc = tmp_path / "board.md"
    doc.write_text(_long_page("---\nsections: collapsible\n---\n"))

    def check(page) -> None:
        page.locator("#h-first button").wait_for()
        page.get_by_text(
            "Paragraph 40 of the first section."
        ).scroll_into_view_if_needed()
        top = page.locator("#blk-first").evaluate("e => e.getBoundingClientRect().top")
        assert 0 <= top <= 50

    _served(doc, check)


def test_page_without_the_key_has_no_toggles(tmp_path: Path) -> None:
    doc = tmp_path / "plain.md"
    doc.write_text(_long_page(""))

    def check(page) -> None:
        assert page.locator("button[data-section-toggle]").count() == 0
        assert (
            page.locator("#blk-first").evaluate("e => getComputedStyle(e).position")
            != "sticky"
        )

    _served(doc, check)
