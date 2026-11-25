"""Input components `ranking` and `slider`."""

from __future__ import annotations

import html
import json
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from ui_fence import block_host

from tavle import PageServer, answer_schema, check, fold, make_read_only, read_rows

HOSTILE = '<script>alert(1)</script>"><img src=x onerror=alert(1)>'
DOC = (
    "# Plan\n\nBody.\n\n"
    "```ui\n"
    'order = ranking(question: "Urgency?", items: ["a", {"label": "B", '
    '"detail": "second", "value": "b"}, "c"])\n'
    'conf = slider(label: "Confidence", min: 0, max: 10, step: 2, '
    'labels: ["Low", "High"])\n'
    'frac = slider(label: "Share", min: 0, max: 1, step: 0.1)\n'
    'plain = slider(label: "Plain", min: -5, max: 5)\n'
    "```\n"
)


def rules(line: str) -> list[str]:
    return [e.rule for e in check(f"```ui\n{line}\n```\n")]


def _doc_with(widget: str) -> str:
    return f"# P\n\n```ui\n{widget}\n```\n"


@pytest.mark.parametrize(
    ("line", "rule"),
    [
        ('r = ranking(question: "Q", items: ["a"])', "type"),  # needs two
        ('r = ranking(question: "Q", items: ["a", "a"])', "option-duplicate"),
        (
            'r = ranking(question: "Q", items: [{"label": "A", "value": "b"}, "b"])',
            "option-duplicate",
        ),
        ('r = ranking(items: ["a", "b"])', "missing-key"),
        (
            'r = ranking(question: "Q", items: ["a", "b"], multiple: true)',
            "unknown-key",
        ),
        ('r = ranking(question: "Q", items: ["a", "b\\u0007"])', "type"),
        ('s = slider(label: "L", max: 5)', "missing-key"),
        ('s = slider(label: "L", min: 5, max: 1)', "range"),
        ('s = slider(label: "L", min: 1, max: 1)', "range"),
        ('s = slider(label: "L", min: 0, max: 5, step: 0)', "range"),
        ('s = slider(label: "L", min: 0, max: 5, step: -1)', "range"),
        ('s = slider(label: "L", min: 0, max: 5, step: 9)', "range"),
        ('s = slider(label: "L", min: 0, max: 1000000, step: 1)', "range"),
        ('s = slider(label: "L", min: "a", max: 5)', "type"),
        ('s = slider(label: "L", min: 0, max: 5, labels: ["x"])', "type"),
        ('s = slider(label: "L", min: 0, max: 5, labels: ["x", ""])', "type"),
        ('s = slider(label: "L", min: 0, max: 5, extra: 1)', "unknown-key"),
    ],
)
def test_props_faults(line: str, rule: str) -> None:
    assert rule in rules(line)


def test_check_refuses_a_ranking_whose_answer_could_not_fit() -> None:
    items = ", ".join(f'"{chr(97 + i % 26) * 300}{i}"' for i in range(30))
    assert "size" in rules(f'r = ranking(question: "Q", items: [{items}])')


def test_schemas_carry_the_declared_range_and_items() -> None:
    schema = answer_schema(DOC, "conf")
    assert schema is not None and schema.bounds == (0, 10, 2)
    schema = answer_schema(DOC, "plain")
    assert schema is not None and schema.bounds == (-5, 5, 1)
    ranking = answer_schema(DOC, "order")
    assert ranking is not None and ranking.allowed == ("a", "b", "c")


def test_invalid_props_are_not_answerable() -> None:
    doc = _doc_with('s = slider(label: "L", min: 5, max: 1)')
    assert answer_schema(doc, "s") is None


# ---- markup -----------------------------------------------------------------


# ---- browser ----------------------------------------------------------------


@pytest.fixture
def site(tmp_path: Path) -> Iterator[tuple[PageServer, Path]]:
    doc = tmp_path / "plan.md"
    doc.write_text(DOC)
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server, doc
    server.shutdown()
    server.server_close()
    thread.join(5)


@pytest.fixture(scope="module")
def shared_page(browser_session: Any) -> Any:
    page = browser_session.new_page()
    page.set_default_timeout(10_000)
    return page


def _mount(page: Any, markup: str) -> None:
    anchor = page.locator(".block").first.get_attribute("data-anchor")
    page.evaluate(
        """([markup, anchor]) => {
            const holder = document.createElement('template');
            holder.innerHTML = markup;
            const block = document.createElement('div');
            block.className = 'block';
            block.dataset.anchor = anchor;
            block.append(holder.content);
            document.querySelector('main[data-role="page"]').append(block);
        }""",
        [markup, anchor],
    )


def _answers(doc: Path) -> list[dict[str, Any]]:
    return [r for r in fold(read_rows(doc)) if r.get("kind") == "answer"]


def _open(page: Any, server: PageServer) -> None:
    page.route("**/events", lambda route: route.abort())
    page.goto(f"http://127.0.0.1:{server.port}/")
    page.wait_for_selector("main[data-role='page'] .block")
    page.wait_for_timeout(300)


@pytest.mark.slow
def test_browser_ranking_buttons_drag_and_announcement(
    shared_page: Any, site: tuple[PageServer, Path]
) -> None:
    server, doc = site
    page = shared_page
    _open(page, server)
    page.wait_for_selector(".ranking[data-hydrated]")

    # keyboard path: focus the move-down button of `a` and press Enter
    page.locator("[aria-label='Move a down']").focus()
    page.keyboard.press("Enter")
    page.locator(".ranking-live", has_text="a is at position 2 of 3.").wait_for()
    row_display = page.eval_on_selector(
        ".ranking-row", "r => getComputedStyle(r).display"
    )
    assert row_display == "list-item"  # keeps the numbered marker
    assert (
        page.evaluate("document.activeElement.getAttribute('aria-label')")
        == "Move a down"
    )
    page.keyboard.press("Enter")
    page.locator("[aria-label='Move c up']").click()
    ids = page.eval_on_selector_all(
        ".ranking-row", "rows => rows.map(r => r.dataset.id)"
    )
    assert ids == ["c", "b", "a"]  # a moved down twice, then c up one
    box = page.locator(".ranking-move").first.bounding_box()
    assert box["width"] >= 44 and box["height"] >= 44

    # at the end of the list a repeated press still announces, with a changed text
    page.locator("[aria-label='Move a down']").click()
    page.locator(".ranking-live", has_text="Already last.").wait_for()
    page.locator("[aria-label='Move a down']").click()
    page.locator(".ranking-live", has_text="Already last.").wait_for()
    page.locator("[aria-label='Move a up']").click()
    page.locator("[aria-label='Move B (b) up']").click()
    assert page.eval_on_selector_all(
        ".ranking-row", "r => r.map(x => x.dataset.id)"
    ) == ["c", "b", "a"]

    # drag the last row above the first
    rows = page.locator(".ranking-row")
    first = page.eval_on_selector(".ranking-row", "r => r.dataset.id")
    rows.last.drag_to(rows.first)
    after = page.eval_on_selector_all(
        ".ranking-row", "rows => rows.map(r => r.dataset.id)"
    )
    assert sorted(after) == ["a", "b", "c"] and after[1] == first

    page.locator(".ranking-send").focus()
    page.keyboard.press("Enter")
    page.locator(".ranking-state", has_text="Sent").wait_for()
    assert page.evaluate("document.activeElement.className") == "ranking-send"
    # while controls are paused (a send in flight) a drag must not start
    cancelled = page.evaluate(
        """() => {
            const list = document.querySelector('.ranking-list');
            list.querySelector('.ranking-move').disabled = true;
            const event = new Event('dragstart', { bubbles: true, cancelable: true });
            list.firstElementChild.dispatchEvent(event);
            list.querySelector('.ranking-move').disabled = false;
            return event.defaultPrevented;
        }"""
    )
    assert cancelled
    sent = [r["value"] for r in _answers(doc) if r["item"] == "order"]
    assert sent == [after]


@pytest.mark.slow
def test_browser_slider_needs_a_move_then_posts_and_read_only_stays_inert(
    shared_page: Any, site: tuple[PageServer, Path]
) -> None:
    server, doc = site
    page = shared_page
    _open(page, server)
    conf = page.locator(".slider", has=page.locator("[data-item='conf']"))
    page.wait_for_selector(".slider[data-hydrated]")

    conf.locator(".slider-send").click()
    assert "Move the slider" in conf.locator(".slider-error").inner_text()
    assert page.evaluate("document.activeElement.type") == "range"
    assert (
        conf.locator(".slider-input").get_attribute("aria-describedby")
        == "slider-error-conf"
    )
    box = conf.locator(".slider-input").bounding_box()
    assert box["height"] >= 44

    # the unmoved thumb sits mid-scale (no clamp before min and max exist)
    assert conf.locator(".slider-input").input_value() not in ("0", "10")
    conf.locator(".slider-input").focus()
    page.keyboard.press("Home")
    for _ in range(3):
        page.keyboard.press("ArrowRight")
    assert conf.locator(".slider-value").inner_text() == "6"
    conf.locator(".slider-send").click()
    conf.locator(".slider-state", has_text="Sent").wait_for()
    assert [r["value"] for r in _answers(doc) if r["item"] == "conf"] == [6]

    # hostile data-props: a missing range refuses to send and posts nothing
    bad = html.escape(json.dumps({"min": "x", "step": -1}), quote=True)
    page.evaluate(
        """(markup) => {
            const holder = document.createElement('template');
            holder.innerHTML = markup;
            document.querySelector('.block').append(holder.content);
        }""",
        f'<div class="vb slider" data-component="slider" data-props="{bad}">'
        '<form class="slider-item" data-item="evil">'
        '<input type="range" class="slider-input">'
        '<button type="submit" class="evil-send">x</button>'
        '<span class="slider-state"></span><p class="slider-error"></p></form></div>',
    )
    page.locator(".evil-send").click()
    assert not [r for r in _answers(doc) if r["item"] == "evil"]

    # read-only markup: controls stay disabled and the drag stays off
    _mount(
        page,
        make_read_only(
            block_host("ranking", {"question": "Q", "items": ["a", "b"]}, "ro")
        ),
    )
    page.wait_for_selector(".ranking[data-hydrated]:has([data-item='ro'])")
    assert page.locator("[data-item='ro'] .ranking-move").first.is_disabled()
    drag = page.eval_on_selector_all(
        "[data-item='ro'] .ranking-row", "rows => rows.map(r => r.draggable)"
    )
    assert drag == [False, False]


# ---- review 01 fixes ----------------------------------------------------------


@pytest.mark.slow
def test_browser_missing_inputs_helpers_show_a_failure(
    shared_page: Any, site: tuple[PageServer, Path]
) -> None:
    from tavle.shell import UI_STATIC

    server, _ = site
    page = shared_page
    source = UI_STATIC.joinpath("inputs_runtime.js").read_text()
    stale = source.replace("ctx.inputs = Object.freeze(", "Object.freeze(")
    assert stale != source
    page.route(
        "**/static/inputs_runtime.js",
        lambda route: route.fulfill(body=stale, content_type="text/javascript"),
    )
    errors: list[str] = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    _open(page, server)
    page.locator(".slider-error", has_text="could not start").first.wait_for()
    assert any("inputs is missing" in e for e in errors)
    page.unroute("**/static/inputs_runtime.js")


@pytest.mark.slow
def test_browser_slider_valuetext_starts_unchosen(
    shared_page: Any, site: tuple[PageServer, Path]
) -> None:
    server, _ = site
    page = shared_page
    _open(page, server)
    conf = page.locator(".slider", has=page.locator("[data-item='conf']"))
    page.wait_for_selector(".slider[data-hydrated]")
    assert (
        conf.locator(".slider-input").get_attribute("aria-valuetext")
        == "Not chosen yet"
    )
    # the unmoved thumb sits mid-scale (no clamp before min and max exist)
    assert conf.locator(".slider-input").input_value() not in ("0", "10")
    conf.locator(".slider-input").focus()
    page.keyboard.press("Home")
    # the native value says the same, so the runtime drops aria-valuetext
    assert conf.locator(".slider-input").get_attribute("aria-valuetext") is None
    assert conf.locator(".slider-input").input_value() == "0"
