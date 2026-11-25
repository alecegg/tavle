# ruff: noqa: S106
"""Served and static page assembly: the shell, theme, API base and partial streams."""

import re
from pathlib import Path

import pytest

from tavle import append_comment, assemble_static
from tavle.page import template
from tavle.page.assemble import drop_pending_tail, parse_page_stream
from tavle.serve.assemble_served import assemble, assemble_page
from tavle.serve.serve import render_document

FIXTURE = Path(__file__).parent / "fixtures" / "page-basic.md"


@pytest.fixture
def doc(tmp_path: Path) -> Path:
    path = tmp_path / "page.md"
    path.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def test_served_page_keeps_the_existing_shell(doc: Path) -> None:
    out = assemble_page(doc, token='t"k')
    assert out.startswith('<!doctype html><html lang="en"><head><meta charset="utf-8">')
    assert '<meta name="tavle-token" content="t&quot;k"><title>page.md</title>' in out
    scripts = re.findall(r'<script src="([^"]+)" defer></script>', out)
    assert scripts == [
        f"/static/{n}"
        for n in (
            "components.js",
            "app.js",
            "blocks.js",
            "inputs_fields.js",
            "inputs_widgets.js",
            "inputs_runtime.js",
            "recap.js",
            "inputs_ordered.js",
        )
    ]
    assert '<main data-role="page">' in out and out.endswith("</main></body></html>")


def test_render_document_is_the_assembler(doc: Path) -> None:
    assert render_document(doc, "tok") == assemble_page(doc, token="tok")


def test_served_page_includes_comment_threads(doc: Path) -> None:
    append_comment(doc, "basic-page/1", "Some text", "note <x>")
    out = assemble_page(doc, token="tok")
    assert 'class="thread"' in out and "note &lt;x&gt;" in out


def test_source_html_is_escaped(doc: Path) -> None:
    out = assemble_page(doc, token="tok")
    assert "<b>" not in out and "&lt;b&gt;" in out


def test_assemble_exposes_part_map(doc: Path) -> None:
    assert assemble(doc, token="tok").parts == {}


def test_served_page_matches_golden_from_before_the_assembler(tmp_path: Path) -> None:
    # page-basic.served.html: render_document at 2049399c5, plus the components.js tag
    page = tmp_path / "page-basic.md"
    page.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    golden = FIXTURE.with_name("page-basic.served.html").read_text(encoding="utf-8")
    assert assemble_page(page, token="golden-token") == golden


def _page(newline: str) -> str:
    lines = [
        "# T",
        "",
        "```ui",
        "a = flow()",
        'b = table(s: "x",',
        "  rows: [1,",
        "  2])",
        "c = flow()",
        "```",
        "",
        "tail text",
    ]
    return newline.join(lines) + newline


def _ids(text: str) -> list[str]:
    return [b.anchor for b in parse_page_stream(text, "p.md").blocks]


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_partial_every_cut_offset_never_raises_and_blocks_are_a_prefix(
    newline: str,
) -> None:
    text = _page(newline)
    full = _ids(text)
    # a cut inside the opener is a stray paragraph, not a block prefix
    start = text.index("```ui") + len("```ui")
    for cut in range(start, len(text) + 1):
        ids = _ids(text[:cut])
        assert ids == full[: len(ids)], cut
        assert drop_pending_tail(text[:cut]) is not None
    assert drop_pending_tail(text) == text


def test_partial_page_drops_unfinished_ui_statement() -> None:
    text = '# T\n\n```ui\na = flow()\nb = table(rows: [1, 2,\n  "x'
    assert drop_pending_tail(text) == "# T\n\n```ui\na = flow()\n```\n"
    body = parse_page_stream(text, "p.md").body
    assert "table" not in body and "rows" not in body


@pytest.mark.parametrize(
    "text",
    [
        "```ui\na = flow()\n```\ntext",
        "plain text",
        "~~~md\n```ui\na = f(\n",  # ui fence nested in a longer outer fence
        "````md\n```ui\na = f(\n",
    ],
)
def test_partial_text_without_open_ui_fence_is_unchanged(text: str) -> None:
    assert drop_pending_tail(text) == text


@pytest.mark.parametrize("opener", ["~~~ui", "  ```ui", "```ui"])
def test_partial_other_fence_forms(opener: str) -> None:
    fence = opener.strip()[:3]
    text = f"{opener}\na = flow()\nb = t(rows: [1,\n"
    assert drop_pending_tail(text) == f"{opener}\na = flow()\n{fence}\n"


def test_partial_cut_at_opener_without_newline_is_dropped_cleanly() -> None:
    assert drop_pending_tail("```ui") == "```ui"
    assert "```ui```" not in drop_pending_tail("# T\n```ui")


API_BASE = "/api/pages/plans/p/plan.md"


def test_api_base_page_posts_to_serve_without_a_token(doc: Path) -> None:
    out = assemble_page(doc, token="tok", api_base=API_BASE)
    assert (
        f'<body data-api-base="{API_BASE}" data-page-url="/pages/plans/p/plan.md">'
        in out
    )
    assert "tavle-token" not in out and "tok" not in out.split("<body")[0]
    assert render_document(doc, "tok", API_BASE) == out


def test_default_page_has_no_api_base_attributes(doc: Path) -> None:
    out = assemble_page(doc, token="tok")
    assert "data-api-base" not in out and "data-page-url" not in out
    assert "<body><main" in out


def _static(name: str) -> str:
    path = Path(template.__file__).parent / "static" / name
    return path.read_text(encoding="utf-8")


def test_page_scripts_gate_every_server_call_on_the_api_base() -> None:
    app, recap, menu = _static("app.js"), _static("recap.js"), _static("menu.js")
    assert "fetch(apiBase + '/comments'" in app
    assert "fetch(apiBase + path" in app and "fetch(apiBase + '/comments'" in recap
    assert "fetch(pageUrl" in app and "fetch('/'" not in app
    # app.js owns the header name; both scripts send it only on the non-api-base
    # branch. EventSource only without a base.
    header_entry = "[globalThis.tavlePageParts.tokenHeader]: ctx.token"
    assert app.count("X-Tavle-Token") == 1 and "X-Tavle-Token" not in recap
    assert app.count(header_entry) == 1 and recap.count(header_entry) == 1
    assert "if (!apiBase) {\n    const events = new EventSource('/events');" in app
    assert "tavle-refresh" in app
    assert "apiBase ? [] :" in app and "readOnly: Boolean(apiBase)" in app
    assert "handlers.readOnly" in menu


def test_answer_threads_carry_item_value_and_latest(tmp_path: Path) -> None:
    path = tmp_path / "d.md"
    path.write_text(
        '# D\n\n```ui id=ship\nship = decision(question: "Ship?")\n```\n',
        encoding="utf-8",
    )
    for value in ("approved", "denied"):
        append_comment(
            path,
            "ship",
            "",
            f"{value}: ship",
            extra={"kind": "answer", "item": "ship", "value": value},
        )
    out = assemble_page(path, token="t")
    flags = re.findall(r'data-item="ship" data-value="(\w+)" data-latest="(\w+)"', out)
    assert flags == [("approved", "false"), ("denied", "true")]


def test_theme_is_first_in_served_and_static_pages(doc: Path) -> None:
    doc.write_text("---\ntheme: harbor\n---\n# Hello\n", encoding="utf-8")
    assert (
        '<main data-role="page"><link rel="stylesheet" data-vd-theme'
        in assemble_page(doc, token="tok")
    )
    assert '<main data-role="page"><style data-vd-theme>' in assemble_static(doc)


def test_invalid_theme_serves_error_and_content(doc: Path) -> None:
    doc.write_text("---\ntheme: nonexistent\n---\n# Hello\n", encoding="utf-8")
    output = assemble_page(doc, token="tok")
    assert '<main data-role="page"><p class="vd-theme-error" role="alert">' in output
    assert "nonexistent" in output and "Hello" in output
