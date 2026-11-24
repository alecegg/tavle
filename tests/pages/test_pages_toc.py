import re
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from ui_paths import UI_STATIC_DIR

from varde.pages.render import render_page
from varde.pages.serve import PageServer
from varde.pages.toc import toc_entries, toc_html

CSS_DIR = Path(__file__).resolve().parents[2] / "src/varde/pages/static/css"
UI_CSS_DIR = UI_STATIC_DIR / "css"


def _nav(*headings: tuple[int, str, str]) -> str:
    return toc_html(toc_entries(headings))


def test_no_headings_emit_nothing() -> None:
    assert _nav() == ""


def test_h1_is_skipped_and_one_heading_is_too_few() -> None:
    assert _nav((1, "Title", "title"), (2, "Only", "only")) == ""


def test_nested_levels_link_to_heading_ids() -> None:
    out = _nav(
        (2, "A", "h-a"),
        (3, "B", "h-b"),
        (4, "C", "h-c"),
        (2, "D", "h-d"),
        (2, "E", "h-e"),
    )
    assert "Contents (4)" in out
    assert '<li class="toc-l2"><a href="#h-a">A</a></li>' in out
    assert '<li class="toc-l3"><a href="#h-b">B</a></li>' in out
    assert "h-c" not in out


def test_hostile_text_is_escaped() -> None:
    out = _nav(
        (2, "<script>x</script>", "h-a"),
        (2, "ok", 'h-b"><i>'),
        (2, "C", "c"),
        (2, "D", "d"),
    )
    assert "<script>" not in out and "&lt;script&gt;" in out
    assert "<i>" not in out


def test_page_with_duplicate_headings_links_unique_ids() -> None:
    page = render_page(
        "# T\n\n## Same\n\n## Same\n\n### Sub\n\n## Fourth\n", "d.md"
    ).body
    assert page.count('<a href="#h-same">') == 1
    assert '<a href="#h-same-2">' in page and '<a href="#h-sub">' in page
    assert "doc-header" not in page  # the page's own H1 is its title
    assert page.index('class="doc-toc"') < page.index('class="block heading"')


def test_page_without_two_headings_has_no_nav() -> None:
    assert "doc-toc" not in render_page("# T\n\n## One\n\ntext\n", "d.md").body


def test_headings_inside_include_are_ignored() -> None:
    body = render_page("# T\n\n## One\n\n<h2>raw</h2>\n", "d.md").body
    assert "doc-toc" not in body


def test_current_section_is_dotted_and_bold_without_an_edge_bar() -> None:
    css = (CSS_DIR / "31-toc.css").read_text()
    rule = re.search(r'\.doc-toc a\[aria-current="location"\] \{([^}]*)\}', css)
    assert rule
    assert "background:" not in rule.group(1)
    dot = re.search(r'\.doc-toc a\[aria-current="location"\]::before \{([^}]*)\}', css)
    assert dot and "background: var(--vd-accent-2)" in dot.group(1)
    assert "font-weight: 700" in rule.group(1)
    assert "border-inline-start" not in css


# --- browser: current section and the phone bar (served page, one page for all) ---

FILLER = "\n\n".join(
    f"Paragraph {n} of filler text so the section is tall." for n in range(30)
)
DOC = (
    "# Report\n\n"
    f"## First\n\n{FILLER}\n\n"
    f"## Second\n\n{FILLER}\n\n"
    '```ui\na = callout(tone: "info", text: "Alpha body")\n```\n\n'
    '```ui\nb = callout(tone: "info", text: "Beta body")\n```\n\n'
    '```ui\nt = tabs(tab: [{"label": "Alpha", "blocks": ["a"]}, '
    '{"label": "Beta", "blocks": ["b"]}])\n```\n\n'
    f"## Third\n\n{FILLER}\n\n"
    f"## Fourth\n\n{FILLER}\n"
)
LINK = '.doc-toc a[href="{}"]'
CURRENT = '.doc-toc a[href="{}"][aria-current="location"]'
ALPHA, BETA = "#vd-ctab-t-1-h", "#vd-ctab-t-2-h"


@pytest.fixture(scope="module")
def toc_page(
    browser_session: Any, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[Any]:
    doc = tmp_path_factory.mktemp("toc") / "report.md"
    doc.write_text(DOC, encoding="utf-8")
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    page = browser_session.new_page(viewport={"width": 1280, "height": 900})
    page.set_default_timeout(10_000)
    problems: list[str] = []
    page.on("pageerror", lambda error: problems.append(str(error)))
    page.goto(f"http://127.0.0.1:{server.port}/")
    page.wait_for_selector(".vd-ctabs-tab")
    yield page
    assert problems == []
    page.close()
    server.shutdown()
    server.server_close()
    thread.join(5)


def _scroll_to(page: Any, selector: str) -> None:
    page.evaluate("(sel) => document.querySelector(sel).scrollIntoView()", selector)


def _current(page: Any) -> list[str]:
    return page.eval_on_selector_all(
        '.doc-toc a[aria-current="location"]', "(links) => links.map((a) => a.hash)"
    )


@pytest.mark.slow
def test_wide_contents_marks_the_section_in_view(toc_page: Any) -> None:
    toc_page.set_viewport_size({"width": 1280, "height": 900})
    _scroll_to(toc_page, "#h-second")
    toc_page.wait_for_selector(CURRENT.format("#h-second"))
    _scroll_to(toc_page, "#h-third")
    toc_page.wait_for_selector(CURRENT.format("#h-third"))
    assert _current(toc_page) == ["#h-third"]


@pytest.mark.slow
def test_marker_follows_a_section_replaced_by_a_live_update(toc_page: Any) -> None:
    toc_page.set_viewport_size({"width": 1280, "height": 900})
    toc_page.evaluate(
        """() => {
            const block = document.querySelector('#h-third').closest('main > *');
            block.replaceWith(block.cloneNode(true));
        }"""
    )
    _scroll_to(toc_page, "#h-third")
    toc_page.wait_for_selector(CURRENT.format("#h-third"))
    assert _current(toc_page) == ["#h-third"]


@pytest.mark.slow
def test_tab_entry_is_current_only_while_its_panel_shows(toc_page: Any) -> None:
    toc_page.set_viewport_size({"width": 1280, "height": 900})
    _scroll_to(toc_page, "#h-second")
    _scroll_to(toc_page, ".vd-ctabs")
    toc_page.wait_for_selector(CURRENT.format(ALPHA))
    assert _current(toc_page) == [ALPHA]
    toc_page.locator(".vd-ctabs-tab", has_text="Beta").click()
    toc_page.wait_for_selector(CURRENT.format(BETA))
    assert _current(toc_page) == [BETA]
    toc_page.locator(".vd-ctabs-tab", has_text="Alpha").click()
    toc_page.wait_for_selector(CURRENT.format(ALPHA))
    assert _current(toc_page) == [ALPHA]


@pytest.mark.slow
def test_current_marker_is_a_dot_not_a_tint_or_edge_bar(toc_page: Any) -> None:
    toc_page.set_viewport_size({"width": 1280, "height": 900})
    _scroll_to(toc_page, "#h-fourth")
    toc_page.wait_for_selector(CURRENT.format("#h-fourth"))
    style = toc_page.locator(CURRENT.format("#h-fourth")).evaluate(
        """(a) => {
            const s = getComputedStyle(a);
            return {
                widths: [
                    s.borderTopWidth, s.borderRightWidth,
                    s.borderBottomWidth, s.borderLeftWidth,
                ],
                tint: s.backgroundColor,
                weight: s.fontWeight,
            };
        }"""
    )
    assert len(set(style["widths"])) == 1
    assert style["tint"] == "rgba(0, 0, 0, 0)"
    assert int(style["weight"]) >= 600


@pytest.mark.slow
def test_phone_contents_bar_stays_in_view_and_closes_on_follow(toc_page: Any) -> None:
    toc_page.set_viewport_size({"width": 390, "height": 844})
    toc_page.wait_for_selector(".doc-toc details:not([open])", state="attached")
    _scroll_to(toc_page, "#h-fourth")
    summary = toc_page.locator(".doc-toc summary")
    box = summary.bounding_box()
    assert box["y"] >= 0 and box["y"] + box["height"] <= 844
    assert box["height"] <= 60
    summary.click()
    assert toc_page.locator(".doc-toc details").get_attribute("open") is not None
    toc_page.locator(LINK.format("#h-second")).click()
    toc_page.wait_for_selector(".doc-toc details:not([open])", state="attached")
    top = toc_page.eval_on_selector("#h-second", "(h) => h.getBoundingClientRect().top")
    bar = summary.bounding_box()
    assert bar["y"] + bar["height"] <= top < 200


@pytest.mark.slow
def test_contents_bar_is_hidden_in_print(toc_page: Any) -> None:
    toc_page.emulate_media(media="print")
    try:
        assert (
            toc_page.eval_on_selector(".doc-toc", "(n) => getComputedStyle(n).display")
            == "none"
        )
    finally:
        toc_page.emulate_media(media="screen")


@pytest.mark.slow
def test_top_of_page_marks_the_first_section(toc_page: Any) -> None:
    toc_page.set_viewport_size({"width": 1280, "height": 900})
    toc_page.evaluate("() => window.scrollTo(0, 0)")
    toc_page.wait_for_selector(CURRENT.format("#h-first"))
    assert _current(toc_page) == ["#h-first"]


@pytest.mark.slow
def test_phone_contents_bar_names_the_current_section(toc_page: Any) -> None:
    toc_page.set_viewport_size({"width": 390, "height": 844})
    _scroll_to(toc_page, "#h-fourth")
    toc_page.wait_for_function(
        "() => document.querySelector('.doc-toc .toc-here').textContent === 'Fourth'"
    )


def test_summary_holds_a_slot_for_the_current_section_name() -> None:
    out = _nav((2, "A", "h-a"), (2, "B", "h-b"), (2, "C", "h-c"), (2, "D", "h-d"))
    assert '<span class="toc-here"></span>' in out


def test_the_toc_column_is_reserved_only_on_a_page_with_a_toc() -> None:
    base = (UI_CSS_DIR / "01-base.css").read_text()
    assert "main:has(> .doc-toc) > * { margin-inline:" in base
    assert re.search(r"\nmain \{[^}]*max-inline-size: var\(--vd-doc-width\)", base)


NO_TOC_DOC = "# Plain\n\ntext\n"


@contextmanager
def _served(tmp_path: Path, text: str) -> Iterator[PageServer]:
    doc = tmp_path / "doc.md"
    doc.write_text(text, encoding="utf-8")
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)


def _open(page: Any, server: PageServer, width: int) -> None:
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(f"http://127.0.0.1:{server.port}/")
    page.wait_for_selector("main .block")


@pytest.mark.slow
def test_page_without_a_toc_is_centred_with_no_empty_gutter(
    toc_page: Any, tmp_path: Path
) -> None:
    with _served(tmp_path, NO_TOC_DOC) as server:
        _open(toc_page, server, 1280)
        centre = toc_page.eval_on_selector(
            "main .block",
            "(b) => {"
            " const r = b.getBoundingClientRect(); return r.left + r.width / 2; }",
        )
    assert centre == pytest.approx(1280 / 2, abs=1)
