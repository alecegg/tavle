"""Plan board table controls."""

import threading
from pathlib import Path

import pytest
from browser_args import BROWSER_ARGS
from playwright.sync_api import sync_playwright

from tavle import PageServer


@pytest.mark.parametrize("count", [12, 17])
def test_toolbar_order(tmp_path: Path, count: int) -> None:
    rows = ", ".join(f'["Row {i}"]' for i in range(count))
    doc = tmp_path / "table.md"
    doc.write_text(
        "# Tables\n\n```ui id=example\n"
        f'example = table(columns: ["Name"], rows: [{rows}])\n```\n'
    )
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=BROWSER_ARGS)
            try:
                page = browser.new_page(viewport={"width": 1024, "height": 900})
                page.route("**/events", lambda route: route.abort())
                page.goto(f"http://127.0.0.1:{server.port}/")
                bar = page.locator(".vb-filterbar")
                bar.wait_for()
                assert bar.is_visible()
                assert bar.evaluate(
                    "e => e.nextElementSibling.classList.contains('vb-scroll')"
                )
                more = page.locator(".vb-more")
                assert more.count() == (1 if count == 17 else 0)
                if count == 17:
                    assert more.evaluate(
                        "e => e.previousElementSibling.classList.contains('vb-scroll')"
                    )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)
