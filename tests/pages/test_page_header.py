"""Page header strip: chip, plan, commit, links, reading time, escaping."""

from __future__ import annotations

from pathlib import Path

import pytest
from ui_paths import UI_STATIC_DIR

from varde.pagelib.page.header import (
    count_words,
    header_html,
    parse_links,
    reading_minutes,
    status_tone,
)
from varde.pagelib.page.render import render_page

FIXTURES = Path(__file__).parent / "fixtures" / "widgets"


def _header(front: str, body: str = "# T\n\ntext\n", name: str = "p.md") -> str:
    page = render_page(f"---\n{front}\n---\n\n{body}" if front else body, name).body
    return page[: page.index("</header>")]


@pytest.mark.parametrize(
    ("status", "tone", "icon"),
    [
        ("todo", "decision", "ring"),
        ("in-progress", "info", "half"),
        ("review", "warning", "triangle"),
        ("blocked", "risk", "cross"),
        ("DONE", "success", "check"),
        ("mystery", "neutral", "dot"),
    ],
)
def test_chip_icon_word_and_tone(status: str, tone: str, icon: str) -> None:
    assert status_tone(status) == (tone, icon)
    head = _header(f"status: {status}")
    assert f"vd-hdr-chip vd-hdr-{tone}" in head
    assert (
        f'<span class="vd-hdr-glyph vd-hdr-glyph-{icon}" aria-hidden="true"></span>'
        in head
    )
    assert f'<span class="status">{status}</span>' in head


def test_missing_keys_keep_todays_header() -> None:
    head = _header("type: task\nrisk: high")
    assert '<p class="status">type: task · risk: high</p>' in head
    assert "vd-hdr" not in head
    plain = render_page("# T\n", "p.md")
    assert 'class="status"' not in plain.body


def test_status_string_is_unchanged() -> None:
    page = render_page("---\ntype: task\nstatus: done\n---\n\n# T\n", "p.md")
    assert page.status == "type: task · status: done"


def test_plan_defaults_to_doc_name_and_key_wins() -> None:
    assert ">p.md</span>" in _header("status: done")
    assert ">my-plan</span>" in _header("status: done\nplan: my-plan")


def test_commit_is_shortened_with_full_value_in_title() -> None:
    sha = "4739f6f54748f4d62a2d95a1e22c8486a3f21080"
    head = _header(f"commit: {sha}")
    assert f'title="{sha}">4739f6f54</span>' in head


def test_link_filter_drops_unsafe_entries() -> None:
    links = parse_links(
        "javascript:alert(1), /etc/passwd, ../x.md, a.md, sub/b.md, "
        "http://ok.example/p, ftp://x.example/f, https://bad host/x, data:text/html,x"
    )
    assert [href for href, _ in links] == ["a.md", "sub/b.md", "http://ok.example/p"]
    head = _header("links: javascript:alert(1), a.md")
    assert "javascript" not in head
    assert 'href="a.md" rel="noopener"' in head


def test_links_are_capped_and_long_labels_shortened() -> None:
    many = ", ".join(f"p{n}.md" for n in range(20))
    assert len(parse_links(many)) == 8
    ((_, label),) = parse_links("https://example.com/" + "a" * 100)
    assert len(label) <= 40


def test_hostile_text_is_escaped() -> None:
    head = _header(
        'status: <script>x</script>\nplan: <b>"p"</b>\ncommit: <img src=x onerror=y>\n'
        "risk: <i>hi</i>",
        name="<n>.md",
    )
    assert "<script" not in head and "<b>" not in head and "<img" not in head
    assert "<i>" not in head and "&lt;script&gt;" in head
    assert "style=" not in head


@pytest.mark.parametrize(
    ("words", "minutes"), [(0, 1), (1, 1), (200, 1), (201, 2), (400, 2), (401, 3)]
)
def test_reading_time_boundaries(words: int, minutes: int) -> None:
    assert reading_minutes(words) == minutes


def test_word_count_skips_fences_and_counts_tables() -> None:
    lines = [
        "# Title here",
        "",
        "Some prose words.",
        "```ui",
        "a = stats(x: 1)",
        "```",
        "| a | b |",
        "| --- | --- |",
        "| one | two |",
    ]
    assert count_words(lines) == 2 + 3 + 2 + 2


def test_reading_time_shown_in_strip() -> None:
    body = "# T\n\n" + "word " * 450
    assert ">3 min<" in _header("status: done", body)
    assert ">1 min<" in _header("status: done")


def test_header_html_is_pure_and_closed() -> None:
    out = header_html({"status": "done"}, "n", 10, titled=False)
    assert out.startswith('<header class="doc-header"><p class="doc-name">n</p>')
    assert out.endswith("</header>")


def test_file_name_shows_only_on_a_page_without_an_h1() -> None:
    untitled = render_page("text only\n\n## Part\n", "p.md").body
    assert (
        '<header class="doc-header"><p class="doc-name">p.md</p></header>' in untitled
    )
    titled = render_page("# Own title\n\ntext\n", "p.md").body
    assert "doc-header" not in titled
    assert "doc-name" not in titled


def test_h1_inside_a_code_fence_does_not_count_as_a_title() -> None:
    body = render_page("```\n# not a heading\n```\n", "p.md").body
    assert '<p class="doc-name">p.md</p>' in body


def test_titled_page_keeps_its_status_line_and_strip_without_the_name() -> None:
    plain = render_page("---\ntype: task\n---\n\n# T\n", "p.md").body
    assert (
        '<header class="doc-header"><p class="status">type: task</p></header>' in plain
    )
    strip = _header("status: done")
    assert "doc-name" not in strip
    assert "vd-hdr-chip" in strip


def test_fixtures_render_strip() -> None:
    for name in ("page-header.md", "page-header-stress.md"):
        body = render_page((FIXTURES / name).read_text(), name).body
        assert 'class="vd-hdr"' in body
        assert "<script" not in body and "<img" not in body and "<style" not in body


def test_iso_dates_are_wrapped_so_they_cannot_split_at_a_hyphen() -> None:
    head = _header("status: todo\nstatus_at: 2026-11-04T09:15 note")
    assert 'status_at: <span class="vd-date">2026-11-04</span>T09:15 note' in head
    css = (UI_STATIC_DIR / "css/50-blocks.css").read_text()
    assert ".vd-date { white-space: nowrap; }" in css


def test_fence_consumers_keep_their_closing_rules():
    from varde.pagelib.page.fences import scan_fences
    from varde.pagelib.page.header import count_words
    from varde.pagelib.page.render import strip_comments
    from varde.pagelib.page.select import heading_id_errors

    lines = ["````code", "``` info", "<!-- hidden -->", "```` tail", "# Title {#Bad}"]
    assert count_words(lines) == 1
    assert strip_comments(lines)[2] == "<!-- hidden -->"
    assert heading_id_errors("\n".join(lines))[0][1] == "heading-id-invalid"
    assert scan_fences(lines)[0].end is None
