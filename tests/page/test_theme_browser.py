"""Themes apply to every block across viewports and live updates."""

import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from every_block_page import every_block_page

from tavle import PRESET_NAMES, PageServer, doc_theme

# Computed form of a CSS value, so a token and its resolved value compare equal.
_COMPUTED = (
    "([prop, v]) => { const e = document.createElement('i'); e.style[prop] = v; "
    "document.body.append(e); const c = getComputedStyle(e)[prop]; "
    "e.remove(); return c; }"
)
_ACCENT = (
    "getComputedStyle(document.documentElement).getPropertyValue('--vd-accent').trim()"
)


@pytest.fixture(scope="module")
def shared_page(browser_session: Any) -> Iterator[Any]:
    page = browser_session.new_page()
    try:
        yield page
    finally:
        page.close()


@pytest.mark.slow
@pytest.mark.parametrize("preset", PRESET_NAMES)
@pytest.mark.parametrize("size", [(1280, 900), (390, 844)])
@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_theme_in_browser(
    tmp_path: Path,
    shared_page: Any,
    preset: str,
    size: tuple[int, int],
    scheme: str,
) -> None:
    body = every_block_page(tmp_path)
    doc = tmp_path / "all.md"
    body = doc.read_text()
    doc.write_text(f"---\ntheme: {preset}\n---\n" + body)
    theme = _resolve_theme(doc, {"theme": preset})
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    page = shared_page
    page.set_viewport_size({"width": size[0], "height": size[1]})
    page.emulate_media(color_scheme=scheme)
    errors: list[str] = []

    def on_error(error: Any) -> None:
        errors.append(str(error))

    def on_console(message: Any) -> None:
        if message.type == "error":
            errors.append(message.text)

    page.on("pageerror", on_error)
    page.on("console", on_console)
    try:
        page.goto(f"http://127.0.0.1:{server.port}/", wait_until="networkidle")
        expected = theme.tokens[scheme]["accent"]
        accent = page.evaluate(_ACCENT)
        assert page.evaluate(_COMPUTED, ["color", accent]) == page.evaluate(
            _COMPUTED, ["color", expected]
        )
        heading = page.locator("h1").first.evaluate(
            "e => getComputedStyle(e).fontFamily"
        )
        assert heading == page.evaluate(
            _COMPUTED, ["fontFamily", theme.shared["--vd-font-heading"]]
        )
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert not errors
    finally:
        page.remove_listener("pageerror", on_error)
        page.remove_listener("console", on_console)
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.slow
def test_theme_refresh_without_reload(tmp_path: Path, shared_page: Any) -> None:
    body = every_block_page(tmp_path)
    doc = tmp_path / "all.md"
    body = doc.read_text()
    doc.write_text("---\ntheme: paper\n---\n" + body)
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    page = shared_page
    try:
        page.goto(f"http://127.0.0.1:{server.port}/", wait_until="networkidle")
        page.evaluate("window.themeTestMarker = 42")
        old = page.evaluate(_ACCENT)
        doc.write_text("---\ntheme: harbor\n---\n" + body)
        page.wait_for_function(
            f"old => {_ACCENT} !== old",
            arg=old,
            timeout=15000,
        )
        assert page.evaluate("window.themeTestMarker") == 42
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def _resolve_theme(doc, frontmatter=None):
    text = (
        "---\n"
        + "\n".join(f"{k}: {v}" for k, v in (frontmatter or {}).items())
        + "\n---\n"
    )
    return doc_theme(doc, text)
