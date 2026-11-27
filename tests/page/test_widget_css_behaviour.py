"""Chromium checks of widget and global CSS behaviour on a served page (slow tier).

Each check reads a computed value in the rendered page, not stylesheet text.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from tavle import PageServer

pytestmark = pytest.mark.slow

DOC = (
    "# Plan\n\nBody.\n\n```ui\n"
    'order = ranking(question: "Urgency?", items: ["a", "b"])\n'
    'setup = form(fields: [{"name": "owner", "label": "Owner", "type": "text"}, '
    '{"name": "days", "label": "Days", "type": "number"}])\n'
    'note = comment(label: "Anything?")\n'
    'ship = decision(question: "Ship?", options: ["approve", "comment"])\n'
    "```\n"
)

INPUT_SELECTORS = [
    "textarea.comment-text",
    ".form-field > input[type=number]",
    "textarea.decision-text",
]

BORDER_VAR_JS = (
    "getComputedStyle(document.documentElement).getPropertyValue('--vd-border')"
)
DURATION_VAR_JS = (
    "getComputedStyle(document.documentElement).getPropertyValue('--vd-dur')"
)


@pytest.fixture(scope="module")
def browser_page(browser_session: Any) -> Iterator[Any]:
    page = browser_session.new_page(viewport={"width": 390, "height": 844})
    page.set_default_timeout(10_000)
    yield page
    page.close()


@contextmanager
def served_widgets(page: Any, tmp_path: Path, **media: str) -> Iterator[Any]:
    """Serve DOC with the given media emulation and yield the mounted page."""
    doc = tmp_path / "plan.md"
    doc.write_text(DOC, encoding="utf-8")
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    page.emulate_media(**media)
    try:
        page.goto(f"http://127.0.0.1:{server.port}/")
        page.locator(".ranking-row").first.wait_for()
        yield page
    finally:
        page.emulate_media(forced_colors="none", reduced_motion="no-preference")
        page.goto("about:blank")
        server.shutdown()
        server.server_close()
        thread.join(5)


def test_widget_inputs_compute_at_least_16px(browser_page: Any, tmp_path: Path) -> None:
    with served_widgets(browser_page, tmp_path) as page:
        sizes = {
            selector: page.locator(selector).first.evaluate(
                "el => parseFloat(getComputedStyle(el).fontSize)"
            )
            for selector in INPUT_SELECTORS
        }
    assert all(size >= 16 for size in sizes.values()), sizes


def test_ranking_rows_compute_pan_y_touch_action(
    browser_page: Any, tmp_path: Path
) -> None:
    with served_widgets(browser_page, tmp_path) as page:
        touch = page.locator(".ranking-row").first.evaluate(
            "el => getComputedStyle(el).touchAction"
        )
    assert touch == "pan-y"


def test_forced_colors_block_maps_the_border_token_to_system_colour(
    browser_page: Any, tmp_path: Path
) -> None:
    with served_widgets(browser_page, tmp_path) as page:
        normal = page.evaluate(BORDER_VAR_JS).strip()
    with served_widgets(browser_page, tmp_path, forced_colors="active") as page:
        forced = page.evaluate(BORDER_VAR_JS).strip()
    assert normal != "CanvasText"
    assert forced == "CanvasText"


def test_reduced_motion_block_zeroes_the_duration_token(
    browser_page: Any, tmp_path: Path
) -> None:
    with served_widgets(browser_page, tmp_path) as page:
        normal = page.evaluate(DURATION_VAR_JS).strip()
    with served_widgets(browser_page, tmp_path, reduced_motion="reduce") as page:
        reduced = page.evaluate(DURATION_VAR_JS).strip()
    assert normal != "0s"
    assert reduced == "0s"
