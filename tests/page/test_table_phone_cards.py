"""Responsive card layout for table blocks."""

import threading
from pathlib import Path

import pytest
from browser_args import BROWSER_ARGS
from playwright.sync_api import sync_playwright

from tavle import PageServer

pytestmark = pytest.mark.slow


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
                    # The 240-character word cannot fit a 1024px grid, so the
                    # table shows cards there too (plan-board 1.6).
                    assert row.evaluate("e => getComputedStyle(e).display") == "block"
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


def test_cards_follow_available_width(tmp_path: Path) -> None:
    doc = tmp_path / "path.md"
    doc.write_text(
        "# Paths\n\n```ui id=paths\n"
        'paths = table(columns: ["Name", "Path", "State", "Owner"], '
        'rows: [["Task", "' + "a" * 60 + '", "Open", "Team"]])\n```\n'
    )
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=BROWSER_ARGS)
            try:
                page = browser.new_page(viewport={"width": 700, "height": 900})
                page.route("**/events", lambda route: route.abort())
                page.goto(f"http://127.0.0.1:{server.port}/")
                table = page.locator(".vb-table")
                row = table.locator("tbody tr").first
                assert row.evaluate("e => getComputedStyle(e).display") == "block"
                assert page.locator(".vb-scroll").evaluate(
                    "e => e.scrollWidth <= e.clientWidth"
                )
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= innerWidth"
                )
                page.set_viewport_size({"width": 1400, "height": 900})
                page.wait_for_function(
                    "() => getComputedStyle("
                    "document.querySelector('.vb-table tbody tr'))"
                    ".display === 'table-row'"
                )
                assert page.locator(".vb-scroll").evaluate(
                    "e => e.scrollWidth <= e.clientWidth"
                )
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= innerWidth"
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)


def test_no_javascript_table_scrolls_only_in_region(tmp_path: Path) -> None:
    doc = tmp_path / "table.md"
    doc.write_text(
        "# Table\n\n| One | Two | Three | Four | Five |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| Alpha | Beta | Gamma | Delta | Epsilon |\n"
    )
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=BROWSER_ARGS)
            try:
                context = browser.new_context(
                    viewport={"width": 320, "height": 900}, java_script_enabled=False
                )
                page = context.new_page()
                page.goto(f"http://127.0.0.1:{server.port}/")
                assert page.locator(".scroll").count() == 1
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= innerWidth"
                )
                assert page.locator("table.vb-cards").count() == 0
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)


def test_hidden_rows_are_measured_after_resize(tmp_path: Path) -> None:
    rows = ", ".join(
        f'["Row {i}", "{("a" * 60) if i == 15 else "short"}", "Open", "Team"]'
        for i in range(17)
    )
    doc = tmp_path / "rows.md"
    doc.write_text(
        "# Rows\n\n```ui id=rows\n"
        'rows = table(columns: ["Name", "Path", "State", "Owner"], rows: ['
        + rows
        + "])\n```\n"
    )
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=BROWSER_ARGS)
            try:
                page = browser.new_page(viewport={"width": 700, "height": 900})
                page.route("**/events", lambda route: route.abort())
                page.goto(f"http://127.0.0.1:{server.port}/")
                page.locator(".vb-more").wait_for()
                page.set_viewport_size({"width": 701, "height": 900})
                page.get_by_text("Show all 17 rows").click()
                assert page.locator(".vb-table.vb-cards").count() == 1
                assert page.locator(".vb-scroll").evaluate(
                    "e => e.scrollWidth <= e.clientWidth"
                )
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= innerWidth"
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)


SHADOW_HARNESS = "<!doctype html><body><div id='host'></div></body>"
SHADOW_MOUNT = """async () => {
  const [html, css] = await Promise.all([
    fetch('/').then((r) => r.text()),
    fetch('/static/app.css').then((r) => r.text()),
  ]);
  const parsed = new DOMParser().parseFromString(html, 'text/html');
  const source = parsed.querySelector('main[data-role="page"]');
  const main = document.importNode(source, true);
  const token = parsed.querySelector('meta[name="tavle-token"]').content;
  const style = document.createElement('style');
  style.textContent = css;
  const shadow = document.getElementById('host').attachShadow({ mode: 'open' });
  shadow.append(style, main);
  const { mountPage } = await import('/static/page.js');
  await mountPage(shadow, { pageUrl: '/', token });
  // The bundle boots on the document only; a host mounts client-side blocks itself.
  await new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = '/static/components.js';
    script.onload = resolve;
    script.onerror = reject;
    document.head.append(script);
  });
  globalThis.tavleMountComponents(shadow, window.m, globalThis.tavleComponents);
}"""


def test_cards_in_shadow_root(tmp_path: Path) -> None:
    doc = tmp_path / "path.md"
    doc.write_text(
        "# Paths\n\n```ui id=paths\n"
        'paths = table(columns: ["Name", "Path", "State", "Owner"], '
        'rows: [["Task", "' + "a" * 60 + '", "Open", "Team"]])\n```\n'
    )
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.port}"
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=BROWSER_ARGS)
            try:
                page = browser.new_page(viewport={"width": 700, "height": 900})
                page.route("**/events", lambda route: route.abort())
                page.route(
                    f"{base}/harness",
                    lambda r: r.fulfill(body=SHADOW_HARNESS, content_type="text/html"),
                )
                page.goto(f"{base}/harness")
                page.evaluate(SHADOW_MOUNT)
                page.locator("#host .vb-table.vb-cards").wait_for()
                assert page.locator("#host .vb-scroll").evaluate(
                    "e => e.scrollWidth <= e.clientWidth"
                )
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= innerWidth"
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)
