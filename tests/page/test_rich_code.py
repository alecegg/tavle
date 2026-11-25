"""The code panel: lines, ranges, marks, escaping, highlighting that keeps the text,
plain fenced code, the Copy button and the no-JS panel."""

from __future__ import annotations

import re
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from tavle import PageServer, check_props
from tavle.blocks_render.code import (
    ALIASES,
)

FIXTURES = Path(__file__).parent / "fixtures" / "widgets"
SAMPLES = {
    "python": (
        'def f(x):\n    """doc\n    more"""\n    return f"{x}" + \'a\' # c\n0x1F 3.5e2'
    ),
    "js": "const a = `x\ny`; /* c\nd */ // e\nif (a) { return 1_000; } 'un",
    "json": '{"a": [1, 2.5, true, null], "b": "x\\"y"}',
    "shell": "# c\nfor x in 1 2; do echo \"$x\" 'q'; done # t",
}


def test_aliases_name_only_known_families() -> None:
    assert set(ALIASES.values()) == {"python", "js", "json", "shell"}


def test_spec_validates_props() -> None:
    ok: dict[str, object] = {"language": "python", "source": "x"}
    assert check_props("code", ok, 1) == []
    assert check_props("code", {**ok, "lines": [2, 3], "mark": [1, [2, 3]]}, 1) == []
    assert check_props("code", {**ok, "wrap": True, "numbers": False}, 1) == []
    assert check_props("code", {**ok, "covers": ["a"]}, 1) == []
    for bad in (
        {"lines": [3, 2]},
        {"lines": [0, 2]},
        {"lines": [1]},
        {"mark": []},
        {"mark": ["a"]},
        {"mark": [[3, 1]]},
        {"wrap": "yes"},
        {"numbers": 1},
        {"extra": 1},
    ):
        assert check_props("code", {**ok, **bad}, 1), bad
    assert check_props("code", {"source": "x"}, 1)
    assert check_props("code", {"language": "python"}, 1)


# --- interactions (browser; the lead runs the slow tier) ---


@pytest.fixture(scope="module")
def shared_page(browser_session: Any) -> Any:
    page = browser_session.new_page(viewport={"width": 900, "height": 700})
    page.set_default_timeout(10_000)
    return page


@pytest.fixture
def open_page(tmp_path: Path, shared_page: Any) -> Iterator[Any]:
    doc = tmp_path / "plan.md"
    doc.write_text((FIXTURES / "rich-code.md").read_text(encoding="utf-8"))
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    problems: list[str] = []
    shared_page.on("pageerror", lambda error: problems.append(str(error)))
    shared_page.goto(f"http://127.0.0.1:{server.port}/")
    shared_page.wait_for_selector(".vd-code .vd-code-copy")
    shared_page.wait_for_timeout(600)  # the live refresh rebuilds widgets once
    shared_page.wait_for_selector(".vd-code .vd-code-copy")
    yield shared_page
    assert problems == []
    shared_page.goto("about:blank")
    server.shutdown()
    server.server_close()
    thread.join(5)


@pytest.mark.slow
def test_interact_copy_writes_the_raw_source_and_announces_it(open_page: Any) -> None:
    page = open_page
    page.evaluate(
        "() => { window.__copied = null; Object.defineProperty(navigator, 'clipboard',"
        " {configurable: true, value: {writeText: (t) => { window.__copied = t;"
        " return Promise.resolve(); }}}); }"
    )
    panel = page.locator(".vd-code").first
    raw = panel.get_attribute("data-copy")
    button = panel.get_by_role("button", name="Copy code")
    assert button.bounding_box()["height"] >= 44
    button.click()
    assert page.evaluate("() => window.__copied") == raw
    assert not re.search(r"^\s*\d+\s", raw or "", re.MULTILINE)
    status = panel.locator(".vd-code-status")
    assert "Copied" in status.inner_text()
    assert status.get_attribute("aria-live") == "polite"


@pytest.mark.slow
def test_interact_keyboard_reaches_the_scroll_region(open_page: Any) -> None:
    page = open_page
    region = page.locator(".vd-code").first.locator(".vd-code-scroll")
    page.locator(".vd-code").first.get_by_role("button", name="Copy code").focus()
    page.keyboard.press("Tab")
    assert region.evaluate("(el) => el === document.activeElement")
    assert region.get_attribute("role") == "region"
