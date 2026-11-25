"""Responsive card layout for table blocks."""

import threading
from pathlib import Path

import pytest
from browser_args import BROWSER_ARGS
from playwright.sync_api import sync_playwright

from tavle import PageServer


@pytest.mark.parametrize("width,stack", [(375, None), (375, False), (1024, None)])
def test_table_cards(tmp_path: Path, width: int, stack: bool | None) -> None:
    option = ", stack: false" if stack is False else ""
    doc = tmp_path / "table.md"
    doc.write_text(
        "# Tables\n\n```ui id=example\n"
        'example = table(columns: ["One", "Two", "Three", "Four", "Five"], '
        'rows: [["Alpha", "Beta", "Gamma", "Delta", "Epsilon"], '
        '["A", "B", "C", "D", "E"]]' + option + ")\n```\n"
    )
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=BROWSER_ARGS)
            try:
                page = browser.new_page(viewport={"width": width, "height": 900})
                page.route("**/events", lambda route: route.abort())
                page.goto(f"http://127.0.0.1:{server.port}/")
                table = page.locator(".vb-table")
                table.wait_for()
                row = table.locator("tbody tr").first
                if width == 375 and stack is None:
                    assert row.evaluate("e => getComputedStyle(e).display") == "block"
                    assert (
                        row.evaluate("e => getComputedStyle(e).borderTopWidth") != "0px"
                    )
                    assert row.locator("td").evaluate_all(
                        "es => es.map(e => getComputedStyle(e, '::before').content)"
                    ) == ["none", '"Two"', '"Three"', '"Four"', '"Five"']
                    assert table.evaluate("e => e.scrollWidth <= e.clientWidth")
                    frame = page.locator("section.vb-card")
                    assert frame.evaluate(
                        "e => getComputedStyle(e).borderTopWidth"
                    ) == ("0px")
                else:
                    assert (
                        row.evaluate("e => getComputedStyle(e).display") == "table-row"
                    )
                    if stack is False:
                        assert page.locator(".vb-scroll").evaluate(
                            "e => e.scrollWidth > e.clientWidth"
                        )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)


@pytest.mark.parametrize("width", [375, 1024])
def test_markdown_table_cards(tmp_path: Path, width: int) -> None:
    doc = tmp_path / "table.md"
    doc.write_text(
        "# Tables\n\n| **One** | Two & three | Three | Four | Five |\n"
        "| --- | --- | --- | --- | --- |\n| Alpha | Beta | Gamma | Delta | "
        + "longword" * 30
        + " |\n"
    )
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=BROWSER_ARGS)
            try:
                page = browser.new_page(viewport={"width": width, "height": 900})
                page.route("**/events", lambda route: route.abort())
                page.goto(f"http://127.0.0.1:{server.port}/")
                table = page.locator("table.vb-table-stack")
                row = table.locator("tbody tr").first
                assert row.locator("td").evaluate_all(
                    "es => es.map(e => e.dataset.label)"
                ) == ["One", "Two & three", "Three", "Four", "Five"]
                if width == 375:
                    assert row.evaluate("e => getComputedStyle(e).display") == "block"
                    assert (
                        row.evaluate("e => getComputedStyle(e).borderTopWidth") != "0px"
                    )
                    assert row.locator("td").evaluate_all(
                        "es => es.map(e => getComputedStyle(e, '::before').content)"
                    ) == ["none", '"Two & three"', '"Three"', '"Four"', '"Five"']
                    assert table.evaluate("e => e.scrollWidth <= e.clientWidth")
                    assert table.locator("..").evaluate(
                        "e => e.scrollWidth <= e.clientWidth"
                    )
                else:
                    assert (
                        row.evaluate("e => getComputedStyle(e).display") == "table-row"
                    )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)


@pytest.mark.parametrize("width", [700, 1024])
def test_long_status_and_code_wrap_instead_of_scrolling(
    tmp_path: Path, width: int
) -> None:
    status = "planned after the three changes above, in build order (Sonnet, 46 tasks)"
    doc = tmp_path / "wide.md"
    doc.write_text(
        "# Wide\n\n```ui id=queue\n"
        'queue = table(columns: ["change", "what it covers", "state"], '
        'types: {"state": "status"}, rows: [["varde-reach-reuse", '
        '"Reach from each language project description for every supported '
        'toolchain and build system", '
        f'"{status}"]])\n```\n'
    )
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=BROWSER_ARGS)
            try:
                page = browser.new_page(viewport={"width": width, "height": 900})
                page.route("**/events", lambda route: route.abort())
                page.goto(f"http://127.0.0.1:{server.port}/")
                region = page.locator(".vb-scroll")
                region.wait_for()
                assert region.evaluate("e => e.scrollWidth <= e.clientWidth")
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= innerWidth"
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
