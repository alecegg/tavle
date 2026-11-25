"""A standalone export of component blocks has all code inline, no remote reference.

The browser run of this export is `tavle tests/components/callout.test.js`.
"""

import json
import re
from pathlib import Path

from every_block_page import every_block_page
from test_components_contract import CALLOUTS, FIXTURES, check_fixture

from tavle import COMPONENT_SPECS
from tavle.components import export_page, mount_block
from tavle.page.template import page_css

# one recorded case per code and diff block, checked in `code_diff.test.js`
CODE_DIFF_CASES = {
    "code": "marks",
    "annotated-code": "range-and-kinds",
    "diff": "split-fold-notes",
    "file-tree": "links",
    "change-summary": "titled",
    "deps": "chain",
}


def _code_diff_hosts() -> str:
    hosts = []
    for block, name in CODE_DIFF_CASES.items():
        cases = json.loads((FIXTURES / f"{block}.json").read_text(encoding="utf-8"))
        props = next(case["props"] for case in cases if case["name"] == name)
        hosts.append(mount_block(block, props, name))
    return "".join(hosts)


def export_document(root: Path) -> str:
    main = "".join(
        mount_block("callout", props, str(props["text"])) for props in CALLOUTS.values()
    )
    main += _code_diff_hosts() + every_block_page(root)
    return export_page("pilot", f'<main data-role="page">{main}</main>', page_css())


def test_export_fixture_matches_python_export(tmp_path: Path) -> None:
    check_fixture("export-callout.html", export_document(tmp_path))


def test_export_holds_every_block_type(tmp_path: Path) -> None:
    page = export_document(tmp_path)
    markup = re.sub(r"<script>.*?</script>", "", page, flags=re.DOTALL)
    hosts = set(re.findall(r'data-mithril="([\w-]+)"', markup))
    # an include is expanded into the parts it names; it has no host of its own
    assert hosts == set(COMPONENT_SPECS)
    assert "works" in page and 'class="vb-card vb-error' not in markup


def test_export_is_self_contained(tmp_path: Path) -> None:
    page = export_document(tmp_path)
    markup = re.sub(
        r"<script[^>]*>.*?</script>", "<script></script>", page, flags=re.DOTALL
    )
    for remote in ("src=", "http://", "https://", "@import", "url(", "<link"):
        assert remote not in markup
    # only same-page links (the contents list) may remain
    assert re.findall(r'href="([^"]*)"', markup) == re.findall(
        r'href="(#[^"]*)"', markup
    )
    assert page.count("<script>") == 1 and "window.m=" in page
