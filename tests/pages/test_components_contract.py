"""Component contract: mount hosts, the bundle, and callout as a client-side block.

`fixtures/callout.json` holds the HTML of the former Python callout renderer as a
golden; Vitest (`pages/tests/components/*.test.js`) checks the component against
it. The standalone export fixture is regenerated with
`VARDE_REGEN_FIXTURES=1 uv run pytest pages/tests`.
"""

import html
import os
import re
from pathlib import Path

import pytest
from varde.pages.assemble import assemble_static
from varde.pages.blocks_render.registry import COMPONENTS, PAGE_STATEMENTS
from varde.pages.components import component_bundle, mount_block
from varde.pages.render import render_page

FIXTURES = Path(__file__).parent / "components" / "fixtures"
COMPONENT_FILES = Path(__file__).parents[1] / "src/varde/pages/static/components"
REGEN = os.environ.get("VARDE_REGEN_FIXTURES") == "1"

CALLOUTS: dict[str, dict[str, object]] = {
    "tones-info": {"tone": "info", "text": "Plain note."},
    "tones-decision": {"tone": "decision", "title": "Storage", "text": "Use SQLite."},
    "tones-risk": {"tone": "risk", "text": "One\n\nTwo"},
    "tones-warning": {"tone": "warning", "text": "Careful."},
    "tones-success": {"tone": "success", "title": "Done", "text": "All green."},
    "inline-code": {
        "tone": "info",
        "text": "Use `queue` and `a<b` here, `x` twice `y`.",
    },
    "escaping": {
        "tone": "risk",
        "title": "<b>&\"'",
        "text": "<script>alert(1)</script> & \"q\" 'a'",
    },
    "paragraphs": {
        "tone": "info",
        "text": "\n\nfirst\n  \n\n  second  \n\n\n\nthird\n\n",
    },
    "empty-title": {"tone": "info", "title": "", "text": "Body"},
    "unicode": {"tone": "success", "text": "caf\u00e9 \u2713 \u25c6"},
}


def check_fixture(name: str, text: str) -> None:
    path = FIXTURES / name
    if REGEN:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    assert path.read_text(encoding="utf-8") == text, (
        f"{name} is stale; run with VARDE_REGEN_FIXTURES=1"
    )


def test_mount_block_keeps_props_out_of_the_markup() -> None:
    host = mount_block("callout", {"tone": "info", "text": "</script><b>"}, "fb <i>")
    assert "</script><b>" not in host
    assert "\\u003c/script>" in host
    assert "<noscript><pre" in host and "fb &lt;i&gt;" in host


def test_bundle_registers_callout_without_module_syntax() -> None:
    bundle = component_bundle()
    assert 'components["callout"]' in bundle
    assert "\nexport " not in bundle and "\nimport " not in bundle


@pytest.mark.parametrize(
    "name", sorted(path.name for path in COMPONENT_FILES.glob("*.js"))
)
def test_component_files_have_no_imports(name: str) -> None:
    source = (COMPONENT_FILES / name).read_text(encoding="utf-8")
    assert "\nimport " not in "\n" + source


def test_callout_statement_renders_a_host_with_its_source_as_fallback() -> None:
    doc = '```ui\nn = callout(tone: "info", text: "Hi <b>")\n```\n'
    body = render_page(doc, "t.md").body
    assert 'data-mithril="callout"' in body
    assert "<noscript><pre" in body and "callout(tone: " in body
    assert '"text": "Hi \\u003cb>"' in body
    assert "vd-callout-label" not in body


def test_every_block_but_page_statements_is_a_bundled_component() -> None:
    blocks = set(COMPONENTS) - PAGE_STATEMENTS
    bundled = set(re.findall(r'components\["([^"]+)"\]', component_bundle()))
    assert blocks == bundled - {"shared"}


SOURCE = 'n = callout(tone: "info", title: "A & B", text: "Hi <b>")'


def noscript_text(page_html: str) -> str:
    """The unescaped text of the one `<noscript><pre>` fallback in `page_html`."""
    found = re.findall(
        r'<noscript><pre class="vd-noscript">(.*?)</pre></noscript>',
        page_html,
        flags=re.DOTALL,
    )
    assert len(found) == 1
    return html.unescape(found[0])


def test_served_page_noscript_is_the_markdown_source() -> None:
    body = render_page(f"```ui\n{SOURCE}\n```\n", "t.md").body
    assert noscript_text(body) == SOURCE
    assert "&lt;b&gt;" in body


def test_standalone_export_noscript_is_the_markdown_source(tmp_path: Path) -> None:
    doc = tmp_path / "t.md"
    doc.write_text(f"```ui\n{SOURCE}\n```\n", encoding="utf-8")
    page = assemble_static(doc)
    assert noscript_text(page) == SOURCE
    assert "window.m=" in page
