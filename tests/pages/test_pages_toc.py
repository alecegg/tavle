import re
from pathlib import Path

from varde.pages.render import render_page
from varde.pages.toc import toc_entries, toc_html

CSS_DIR = Path(__file__).resolve().parents[2] / "src/varde/pages/static/css"


def _nav(*headings: tuple[int, str, str]) -> str:
    return toc_html(toc_entries(headings))


def test_no_headings_emit_nothing() -> None:
    assert _nav() == ""


def test_h1_is_skipped_and_one_heading_is_too_few() -> None:
    assert _nav((1, "Title", "title"), (2, "Only", "only")) == ""


def test_nested_levels_link_to_heading_ids() -> None:
    out = _nav((2, "A", "h-a"), (3, "B", "h-b"), (4, "C", "h-c"))
    assert "Contents (2)" in out
    assert '<li class="toc-l2"><a href="#h-a">A</a></li>' in out
    assert '<li class="toc-l3"><a href="#h-b">B</a></li>' in out
    assert "h-c" not in out


def test_hostile_text_is_escaped() -> None:
    out = _nav((2, "<script>x</script>", "h-a"), (2, "ok", 'h-b"><i>'))
    assert "<script>" not in out and "&lt;script&gt;" in out
    assert "<i>" not in out


def test_page_with_duplicate_headings_links_unique_ids() -> None:
    page = render_page("# T\n\n## Same\n\n## Same\n\n### Sub\n", "d.md").body
    assert page.count('<a href="#h-same">') == 1
    assert '<a href="#h-same-2">' in page and '<a href="#h-sub">' in page
    assert page.index('class="doc-toc"') > page.index("</header>")


def test_page_without_two_headings_has_no_nav() -> None:
    assert "doc-toc" not in render_page("# T\n\n## One\n\ntext\n", "d.md").body


def test_headings_inside_include_are_ignored() -> None:
    body = render_page("# T\n\n## One\n\n<h2>raw</h2>\n", "d.md").body
    assert "doc-toc" not in body


def test_current_section_is_tinted_and_bold_without_an_edge_bar() -> None:
    css = (CSS_DIR / "31-toc.css").read_text()
    rule = re.search(r'\.doc-toc a\[aria-current="location"\] \{([^}]*)\}', css)
    assert rule
    assert "background: var(--vd-selected)" in rule.group(1)
    assert "font-weight: 700" in rule.group(1)
    assert "border-inline-start" not in css
