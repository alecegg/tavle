"""Chromium checks of the per-block action menu (slow tier; run by the lead)."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from varde_pages.actions import menu_entries
from varde_pages.serve import PageServer

pytestmark = pytest.mark.slow

DOC = (
    "# Plan\n\nAlpha paragraph.\n\n---\n\nBeta paragraph.\n\n```python\nprint(1)\n```\n"
)
LABELS = {
    "comment": "Comment",
    "suggest": "Suggest",
    "edit": "Edit",
    "copy": "Copy",
    "copy-link": "Copy link",
}


@pytest.fixture(scope="module")
def shared_page(browser_session: Any) -> Any:
    page = browser_session.new_page(viewport={"width": 390, "height": 844})
    page.set_default_timeout(10_000)
    return page


@pytest.fixture
def page(tmp_path: Path, shared_page: Any) -> Iterator[Any]:
    doc = tmp_path / "plan.md"
    doc.write_text(DOC, encoding="utf-8")
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    shared_page.goto(f"http://127.0.0.1:{server.port}/")
    shared_page.wait_for_selector(".menu-btn")
    yield shared_page
    shared_page.goto("about:blank")
    server.shutdown()
    server.server_close()
    thread.join(5)


def alpha(page: Any) -> Any:
    return page.locator(".block", has_text="Alpha").first


def test_one_44px_button_per_block_and_no_old_buttons(page: Any) -> None:
    blocks = page.locator(".block:not(:has(hr))").count()
    assert page.locator(".menu-btn").count() == blocks
    assert page.locator(".block:has(hr) .menu-btn").count() == 0
    old = ", ".join(f".{name}-btn" for name in ("comment", "suggest", "edit"))
    assert page.locator(old).count() == 0
    box = alpha(page).locator(".menu-btn").bounding_box()
    assert box["width"] >= 44 and box["height"] >= 44, box


def test_entries_equal_the_server_table_per_block_type(page: Any) -> None:
    for block in page.locator(".block:has(> .menu-btn)").all():
        block_type = block.get_attribute("data-block-type")
        block.locator(".menu-btn").click()
        labels = page.locator(".menu-item").all_inner_texts()
        expected = menu_entries(block_type, allow_edit=True, in_part=False)
        assert labels == [LABELS[e] for e in expected], block_type
        page.keyboard.press("Escape")


def test_code_block_has_no_suggest(page: Any) -> None:
    code = page.locator('.block[data-block-type="code"]').first
    code.locator(".menu-btn").click()
    assert page.locator('.menu-item[data-entry="suggest"]').count() == 0
    assert page.locator('.menu-item[data-entry="comment"]').count() == 1


def test_keyboard_open_arrows_escape_returns_focus(page: Any) -> None:
    button = alpha(page).locator(".menu-btn")
    button.focus()
    page.keyboard.press("Enter")
    assert page.evaluate("document.activeElement.dataset.entry") == "comment"
    assert page.locator('[role="menu"] [role="menuitem"]').count() >= 3
    page.keyboard.press("ArrowDown")
    assert page.evaluate("document.activeElement.dataset.entry") == "suggest"
    page.keyboard.press("End")
    assert page.evaluate("document.activeElement.dataset.entry") == "copy-link"
    page.keyboard.press("Home")
    assert page.evaluate("document.activeElement.dataset.entry") == "comment"
    page.keyboard.press("Escape")
    assert page.locator('[role="menu"]').count() == 0
    assert page.evaluate("document.activeElement.className") == "menu-btn"


def test_tab_and_outside_tap_close(page: Any) -> None:
    alpha(page).locator(".menu-btn").click()
    page.keyboard.press("Tab")
    assert page.locator('[role="menu"]').count() == 0
    alpha(page).locator(".menu-btn").click()
    page.mouse.click(5, 5)
    assert page.locator('[role="menu"]').count() == 0


def test_comment_entry_opens_the_composer(page: Any) -> None:
    alpha(page).locator(".menu-btn").click()
    page.locator('.menu-item[data-entry="comment"]').click()
    assert page.locator(".composer textarea").count() == 1


def test_copy_link_uses_the_fallback_on_a_non_secure_context(page: Any) -> None:
    page.evaluate("window.__copied = null")
    page.evaluate("Object.defineProperty(navigator, 'clipboard', { value: undefined })")
    page.evaluate(
        "document.execCommand = (c) => { window.__copied ="
        " document.activeElement.value; return true; }"
    )
    block = alpha(page)
    block.locator(".menu-btn").click()
    page.locator('.menu-item[data-entry="copy-link"]').click()
    assert page.evaluate("window.__copied").endswith("#" + block.get_attribute("id"))
    assert page.locator(".menu-live").inner_text() == "Copied"


def shown(page: Any, selector: str) -> bool:
    """True when the first match is drawn (opacity 1), never display:none."""
    return page.locator(selector).first.evaluate(
        "(el) => getComputedStyle(el).opacity === '1'"
    )


def test_buttons_are_hidden_at_rest_but_still_in_the_tab_order(page: Any) -> None:
    page.mouse.move(0, 0)
    buttons = page.locator(".menu-btn")
    assert buttons.count() > 0
    assert not any(
        b.evaluate("(el) => getComputedStyle(el).opacity !== '0'")
        for b in buttons.all()
    )
    assert all(b.evaluate("(el) => el.tabIndex === 0") for b in buttons.all())


def test_hover_and_focus_reveal_only_that_blocks_button(page: Any) -> None:
    page.mouse.move(0, 0)
    block = alpha(page)
    block.hover()
    assert shown(page, ".block:has-text('Alpha') > .menu-btn")
    assert not shown(page, ".block:has-text('Beta') > .menu-btn")
    page.mouse.move(0, 0)
    assert not shown(page, ".block:has-text('Alpha') > .menu-btn")
    block.locator(".menu-btn").focus()
    assert shown(page, ".block:has-text('Alpha') > .menu-btn")


def test_revealed_button_keeps_its_44px_target(page: Any) -> None:
    alpha(page).hover()
    box = alpha(page).locator(".menu-btn").bounding_box()
    assert box["width"] >= 44 and box["height"] >= 44, box


def test_a_mouse_click_leaves_no_button_revealed_after_the_pointer_leaves(
    page: Any,
) -> None:
    alpha(page).locator("p").click()
    page.mouse.move(0, 0)
    assert not shown(page, ".block:has-text('Alpha') > .menu-btn")
