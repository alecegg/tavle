"""Chromium checks of the action menu on a touch device (slow tier).

Its own module: the browser runs single-process, so a touch page needs its own
module-scoped browser session beside the mouse module's.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from varde.pages.serve import PageServer

pytestmark = pytest.mark.slow

DOC = (
    "# Plan\n\nAlpha paragraph.\n\n---\n\nBeta paragraph.\n\n```python\nprint(1)\n```\n"
)


def alpha(page: Any) -> Any:
    return page.locator(".block", has_text="Alpha").first


def shown(page: Any, selector: str) -> bool:
    return page.locator(selector).first.evaluate(
        "(el) => getComputedStyle(el).opacity === '1'"
    )


@pytest.fixture(scope="module")
def shared_page(browser_session: Any) -> Any:
    page = browser_session.new_page(
        viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True
    )
    page.set_default_timeout(10_000)
    return page


@pytest.fixture
def touch_page(tmp_path: Path, shared_page: Any) -> Iterator[Any]:
    doc = tmp_path / "plan.md"
    doc.write_text(DOC, encoding="utf-8")
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    shared_page.goto(f"http://127.0.0.1:{server.port}/")
    shared_page.wait_for_selector(".menu-btn", state="attached")
    yield shared_page
    shared_page.goto("about:blank")
    server.shutdown()
    server.server_close()
    thread.join(5)


def test_touch_tap_reveals_one_button_and_reserves_no_width(touch_page: Any) -> None:
    page = touch_page
    assert page.evaluate("matchMedia('(hover: none)').matches")
    assert not any(
        b.evaluate("(el) => getComputedStyle(el).opacity !== '0'")
        for b in page.locator(".menu-btn").all()
    )
    block = alpha(page)
    width = block.evaluate("(el) => el.getBoundingClientRect().width")
    inner = block.locator("p").evaluate("(el) => el.getBoundingClientRect().width")
    assert inner >= width - 1, (inner, width)
    block.locator("p").tap()
    assert shown(page, ".block:has-text('Alpha') > .menu-btn")
    assert not shown(page, ".block:has-text('Beta') > .menu-btn")
    page.locator(".block:has-text('Beta') p").tap()
    assert shown(page, ".block:has-text('Beta') > .menu-btn")
    assert not shown(page, ".block:has-text('Alpha') > .menu-btn")
    page.touchscreen.tap(5, 5)
    page.locator("h1").tap()
    assert not shown(page, ".block:has-text('Alpha') > .menu-btn")


def test_touch_gutter_tap_at_rest_opens_no_menu_and_revealed_button_opens_it(
    touch_page: Any,
) -> None:
    page = touch_page
    box = alpha(page).locator(".menu-btn").bounding_box()
    page.touchscreen.tap(box["x"] + 5, box["y"] + 5)
    assert page.locator('[role="menu"]').count() == 0
    alpha(page).locator("p").tap()
    alpha(page).locator(".menu-btn").tap()
    assert page.locator('[role="menu"]').count() == 1
    assert page.locator('.menu-item[data-entry="comment"]').count() == 1


TALL = (
    "# Plan\n\n"
    + "\n".join(f"- item {n} [link{n}](https://example.com/{n})" for n in range(120))
    + "\n\nAfter.\n"
)


@pytest.fixture
def tall_page(tmp_path: Path, shared_page: Any) -> Iterator[Any]:
    doc = tmp_path / "plan.md"
    doc.write_text(TALL, encoding="utf-8")
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    shared_page.goto(f"http://127.0.0.1:{server.port}/")
    shared_page.wait_for_selector(".menu-btn", state="attached")
    yield shared_page
    shared_page.goto("about:blank")
    server.shutdown()
    server.server_close()
    thread.join(5)


def scroll_into_the_list(page: Any) -> tuple[float, float]:
    """Scroll so the list's top edge is above the screen; tap its middle."""
    page.evaluate("window.scrollTo(0, 900)")
    top = page.locator(".block[data-block-type='list']").evaluate(
        "(el) => el.getBoundingClientRect().top"
    )
    assert top < -100, top
    return 330.0, 400.0


def test_tap_in_a_long_block_places_the_menu_button_at_the_tap(
    tall_page: Any,
) -> None:
    page = tall_page
    x, y = scroll_into_the_list(page)
    before = page.evaluate("window.scrollY")
    page.touchscreen.tap(x, y)
    box = page.locator(".block[data-block-type='list'] > .menu-btn").bounding_box()
    assert box["y"] >= 0 and box["y"] + box["height"] <= 844, box
    assert abs(box["y"] - y) <= 60 and abs(box["x"] + box["width"] / 2 - x) <= 60, box
    assert page.evaluate("window.scrollY") == before


def test_comment_from_a_tapped_long_block_opens_in_view_without_scrolling(
    tall_page: Any,
) -> None:
    page = tall_page
    x, y = scroll_into_the_list(page)
    before = page.evaluate("window.scrollY")
    page.touchscreen.tap(x, y)
    page.locator(".block[data-block-type='list'] > .menu-btn").tap()
    page.locator('.menu-item[data-entry="comment"]').tap()
    box = page.locator(".composer").bounding_box()
    assert box["y"] >= 0 and box["y"] + box["height"] <= 844, box
    assert page.evaluate("window.scrollY") == before
    page.locator(".composer button", has_text="Cancel").tap()
    assert page.evaluate("window.scrollY") == before
    assert page.locator(".composer").count() == 0


def test_comment_send_keeps_the_scroll_position(tall_page: Any) -> None:
    page = tall_page
    x, y = scroll_into_the_list(page)
    before = page.evaluate("window.scrollY")
    page.touchscreen.tap(x, y)
    page.locator(".block[data-block-type='list'] > .menu-btn").tap()
    page.locator('.menu-item[data-entry="comment"]').tap()
    page.locator(".composer textarea").fill("note")
    page.locator(".composer button", has_text="Send").tap()
    page.wait_for_selector(".thread")
    assert abs(page.evaluate("window.scrollY") - before) <= 2


def test_tapping_a_link_in_a_block_opens_no_menu(tall_page: Any) -> None:
    page = tall_page
    page.evaluate("window.__taps = 0")
    page.evaluate(
        "document.addEventListener('click', (e) => {"
        " if (e.target.closest('a')) { e.preventDefault(); window.__taps++; } })"
    )
    link = page.locator(".block[data-block-type='list'] a").first
    box = link.bounding_box()
    page.touchscreen.tap(box["x"] + 5, box["y"] + box["height"] / 2)
    assert page.evaluate("window.__taps") == 1
    assert not any(
        b.evaluate("(el) => getComputedStyle(el).opacity === '1'")
        for b in page.locator(".menu-btn").all()
    )


def test_touch_button_on_a_code_block_misses_its_copy_button(touch_page: Any) -> None:
    page = touch_page
    code = page.locator(".block[data-block-type='code']")
    box = code.bounding_box()
    page.touchscreen.tap(box["x"] + 20, box["y"] + box["height"] - 12)
    button = code.locator("> .menu-btn").bounding_box()
    for other in code.locator("button:not(.menu-btn)").all():
        spot = other.bounding_box()
        apart = (
            button["x"] + button["width"] <= spot["x"]
            or spot["x"] + spot["width"] <= button["x"]
            or button["y"] + button["height"] <= spot["y"]
            or spot["y"] + spot["height"] <= button["y"]
        )
        assert apart, (button, spot)
