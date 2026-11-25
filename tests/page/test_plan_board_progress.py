"""Progress column type: validation, cell rendering and sorting."""

import threading

import pytest
from browser_args import BROWSER_ARGS
from playwright.sync_api import sync_playwright

from tavle import PageServer
from tavle.blocks.tables import validate_table


def test_progress_cells():
    data = {
        "columns": ["Progress"],
        "types": {"Progress": "progress"},
        "rows": [[[1, 2]], [[3, 6]], [[0, 0]]],
    }
    assert validate_table(data) == []


def test_bad_progress_cells():
    for cell in ([5, 3], "5", [-1, 2], [1.5, 2], [True, 2]):
        data = {
            "columns": ["Progress"],
            "types": {"Progress": "progress"},
            "rows": [[cell]],
        }
        faults = validate_table(data)
        assert len(faults) == 1
        assert faults[0].rule == "type"
        assert "rows[1] 'Progress'" in faults[0].message


@pytest.mark.slow
def test_progress_render_and_sort(tmp_path):
    doc = tmp_path / "progress.md"
    doc.write_text(
        "# Progress\n\n```ui id=example\n"
        'example = table(columns: ["Name", "Progress"], '
        'types: {Progress: "progress"}, '
        'rows: [["A", [1, 2]], ["B", [3, 6]], ["C", [1, 4]], '
        '["D", [3, 4]], ["E", [0, 0]]])\n```\n'
    )
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=BROWSER_ARGS)
            try:
                page = browser.new_page()
                page.route("**/events", lambda route: route.abort())
                page.goto(f"http://127.0.0.1:{server.port}/")
                cells = page.locator("tbody tr td:nth-child(2)")
                cells.first.wait_for()
                assert cells.nth(0).inner_text() == "1 of 2"
                assert cells.nth(1).inner_text() == "3 of 6"
                assert (
                    cells.nth(0).locator(".vb-bar-fill").get_attribute("width")
                    == "50.0"
                )
                assert (
                    cells.nth(1).locator(".vb-bar-fill").get_attribute("width")
                    == "50.0"
                )
                page.get_by_role("button", name="Progress", exact=True).click()
                assert cells.all_inner_texts() == [
                    "0 of 0",
                    "1 of 4",
                    "1 of 2",
                    "3 of 6",
                    "3 of 4",
                ]
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)
