"""Code and diff blocks render client-side: registration, props, hosts, page links.

The component DOM is checked in `pages/tests/components/code_diff.test.js` against
`components/fixtures/<block>.json`, the HTML the former Python renderers produced.
These tests keep the Python side of that contract: the fixture inputs still produce
the recorded props, the blocks render as hosts, and the server-side logic (lexer,
diff rows, folding, links, marker counts, layout) behaves as before.
"""

from __future__ import annotations

import html
import json
import re
import threading
import urllib.request
from pathlib import Path

import pytest
from varde_pages.blocks.change_summary import EMPTY, UNCOUNTED
from varde_pages.blocks_render.annotated_code import annotated_props
from varde_pages.blocks_render.change_summary import change_summary_props
from varde_pages.blocks_render.code import Panel, code_block_props, code_props, tokenize
from varde_pages.blocks_render.containers import fill_containers
from varde_pages.blocks_render.diff import diff_props
from varde_pages.blocks_render.file_tree import (
    code_titles,
    file_links,
    file_tree_props,
    link_file_trees,
)
from varde_pages.blocks_render.registry import COMPONENTS
from varde_pages.components import component_bundle, host_props, mount_block
from varde_pages.graph import deps_layout
from varde_pages.render import render_page
from varde_pages.serve import PageServer

TESTS = Path(__file__).parent
FIXTURES = TESTS / "components" / "fixtures"
WIDGETS = TESTS / "fixtures" / "widgets"
BLOCKS = ("code", "annotated-code", "diff", "file-tree", "change-summary", "deps")
SAMPLES = {
    "python": 'def f(x):\n    """doc\n    more"""\n    return f"{x}" + \'a\' # c\n0x1F',
    "js": "const a = `x\ny`; /* c\nd */ // e\nif (a) { return 1_000; } 'un",
    "json": '{"a": [1, 2.5, true, null], "b": "x\\"y"}',
    "shell": "# c\nfor x in 1 2; do echo \"$x\" 'q'; done # t",
}
BEFORE = "".join(f"line {i}\n" for i in range(1, 31))
AFTER = BEFORE.replace("line 15\n", "line fifteen\n")


def _fixture(name: str) -> list[dict[str, object]]:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def _props_of(block: str, case: dict[str, object]) -> dict[str, object]:
    data = case["input"]
    assert isinstance(data, dict)
    if block == "code":
        return code_block_props(data)
    if block == "annotated-code":
        return annotated_props(data)
    if block == "diff":
        return diff_props(data)
    if block == "deps":
        return deps_layout(data)
    if block == "change-summary":
        found = case["markers"]
        markers = None if found is None else [tuple(m) for m in found]  # type: ignore[attr-defined]
        return change_summary_props(data, markers)  # type: ignore[arg-type]
    props = file_tree_props(data)
    titles = case["titles"]
    assert isinstance(titles, dict)
    paths = [str(entry["path"]) for entry in data["entries"]]
    links = file_links(paths, titles)
    return {**props, "links": links} if links else props


@pytest.mark.parametrize("block", BLOCKS)
def test_block_is_client_side_and_bundled(block: str) -> None:
    assert COMPONENTS[block].props is not None
    assert f'components["{block}"]' in component_bundle()


@pytest.mark.parametrize("block", BLOCKS)
def test_fixture_inputs_still_produce_the_recorded_props(
    block: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # the "big" and "truncated" cases were recorded with small caps
    monkeypatch.setattr("varde_pages.blocks.diff_rows.MAX_ROWS", 20)
    monkeypatch.setattr("varde_pages.blocks_render.diff.MAX_ROWS", 20)
    monkeypatch.setattr("varde_pages.graph._MAX_NODES", 12)
    monkeypatch.setattr("varde_pages.graph._MAX_EDGES", 10)
    cases = _fixture(block)
    assert len(cases) >= 5
    for case in cases:
        assert _props_of(block, case) == case["props"], case["name"]
        assert isinstance(case["html"], str) and case["html"]


def test_statements_render_hosts_with_their_source_as_fallback() -> None:
    doc = (
        "```ui\n"
        'c = code(language: "py", source: "x = 1 <b>\\n", mark: [1])\n'
        'a = annotated-code(filename: "f.py", language: "py", source: "x\\n",'
        ' notes: [{lines: 1, note: "n"}])\n'
        'd = diff(before: "a\\n", after: "b\\n")\n'
        'f = file-tree(entries: [{path: "a/b.py"}])\n'
        "s = change-summary()\n"
        'g = deps(edges: {a: ["b"]})\n'
        "```\n"
    )
    body = render_page(doc, "t.md").body
    for block in BLOCKS:
        assert f'data-mithril="{block}"' in body, block
    assert "vb-error" not in body and "<noscript><pre" in body
    assert "x = 1 &lt;b&gt;" in body and "<b>" not in body


# --- code ---


@pytest.mark.parametrize("language", sorted(SAMPLES))
def test_highlighting_round_trips_the_source(language: str) -> None:
    source = SAMPLES[language]
    assert "".join(text for _, text in tokenize(source, language)) == source
    lines = code_props(source, language)["lines"]
    rebuilt = "\n".join("".join(text for _, text in line) for line in lines)  # type: ignore[attr-defined]
    assert rebuilt == source
    assert any(kind for line in lines for kind, _ in line)  # type: ignore[attr-defined]


@pytest.mark.parametrize("language", ["", "cobol", "<b>", "markdown"])
def test_unknown_or_missing_language_is_plain(language: str) -> None:
    source = "def f(): return 1  # not coloured"
    assert tokenize(source, language) == [("", source)]
    assert code_props(source, language)["lines"] == [[["", source]]]


def test_lines_window_is_clamped_and_numbers_start_at_from() -> None:
    source = "\n".join(f"l{i}" for i in range(1, 11))

    def shown(window: list[int]) -> tuple[object, int]:
        props = code_props(source, "", Panel(window=window))
        return props["first"], len(props["lines"])  # type: ignore[arg-type]

    assert shown([4, 6]) == (4, 3)
    assert shown([8, 99]) == (8, 3)
    assert shown([50, 60]) == (10, 1)


def test_marks_are_clipped_to_the_shown_lines_and_named_in_words() -> None:
    source = "\n".join(f"l{i}" for i in range(1, 21))
    props = code_props(source, "py", Panel(mark=[2, [5, 7], [19, 90]]))
    assert props["marked"] == [2, 5, 6, 7, 19, 20]
    assert props["note"] == "Marked lines 2, 5-7, 19-20"
    assert code_props(source, "", Panel(mark=[3]))["note"] == "Marked line 3"
    assert code_props(source, "", Panel(mark=[99]))["note"] == ""
    many = Panel(mark=[[i, i] for i in range(1, 400, 2)])
    big = "\n".join("x" for _ in range(500))
    assert "and 192 more" in str(code_props(big, "", many)["note"])


def test_plain_fenced_code_is_a_code_host() -> None:
    body = render_page("```py\nx = <b>\n```\n\n```\nplain\n```\n", "t.md").body
    assert body.count('data-mithril="code"') == 2
    assert [p["langClass"] for p in host_props(body, "code")] == ["py", ""]
    assert "<script>x" not in render_page("```\n<script>x</script>\n```\n", "t.md").body


def test_the_unscripted_page_shows_the_source_as_text(tmp_path: Path) -> None:
    doc = tmp_path / "plan.md"
    doc.write_text((WIDGETS / "rich-code.md").read_text(encoding="utf-8"))
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{server.port}/") as reply:
            body = reply.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)
    assert "vd-code-copy" not in body
    fallback = re.search(r"<noscript><pre[^>]*>(.*?)</pre>", body, re.DOTALL)
    assert fallback and "queue.py" in fallback[1]


# --- annotated-code ---


def _annotated(notes: list[dict[str, object]], **more: object) -> dict[str, object]:
    source = "".join(f"l{i} = {i}\n" for i in range(1, 41))
    data = {"filename": "f.py", "language": "py", "source": source, "notes": notes}
    return annotated_props({**data, **more})


def test_annotated_notes_are_numbered_and_clamped_with_words_for_kinds() -> None:
    notes = [
        {"lines": "39-90", "note": "a", "kind": "warn"},
        {"lines": 3, "note": "b"},
    ]
    props = _annotated(notes)
    found = props["notes"]
    assert [(n["number"], n["start"], n["end"]) for n in found] == [  # type: ignore[index]
        (1, 3, 3),
        (2, 39, 40),
    ]
    assert (found[1]["glyph"], found[1]["word"]) == ("!", "Warning")  # type: ignore[index]
    assert props["copy"].endswith("2. lines 39-40: a")  # type: ignore[attr-defined]


def test_annotated_quiet_stretches_fold_unless_collapse_is_off() -> None:
    notes: list[dict[str, object]] = [{"lines": 20, "note": "n"}]
    assert _annotated(notes)["folds"] == [[1, 16], [24, 40]]
    assert _annotated(notes, collapse=False)["folds"] == []
    assert _annotated([])["notes"] == []


def test_annotated_columns_count_notes_sharing_a_start_line() -> None:
    crowded: list[dict[str, object]] = [{"lines": 2, "note": f"n{i}"} for i in range(3)]
    assert _annotated(crowded)["columns"] == 3
    assert _annotated([])["columns"] == 1


# --- diff ---


def test_diff_header_names_the_change_and_counts_lines() -> None:
    same = diff_props({"before": "a\nb\n", "after": "a\nb\n"})
    assert (same["count"], same["change"]) == ("No changes", "")
    added = diff_props({"filename": "n.txt", "before": "", "after": "x\ny\n"})
    assert (added["change"], added["count"]) == ("added", "+2 added, -0 removed")
    assert added["blocks"][0]["header"] == "@@ -0,0 +1,2 @@"  # type: ignore[index]
    removed = diff_props({"before": "x\n", "after": ""})
    assert removed["change"] == "removed"


def test_diff_copy_is_the_unified_diff_and_a_patch_copies_itself() -> None:
    copy = str(
        diff_props({"filename": "f.txt", "before": BEFORE, "after": AFTER})["copy"]
    )
    assert copy.startswith("--- a/f.txt\n+++ b/f.txt\n@@ ")
    assert "-line 15\n+line fifteen" in copy
    patch = "--- a/o.py\n+++ b/n.py\n@@ -1,2 +1,2 @@\n a\n-b\n+c"
    props = diff_props({"patch": patch})
    assert props["copy"] == patch
    assert (props["name"], props["change"], props["was"]) == ("n.py", "renamed", "o.py")


def test_diff_folds_long_unchanged_runs_and_keeps_noted_lines() -> None:
    props = diff_props({"before": BEFORE, "after": AFTER})
    kinds = [block["kind"] for block in props["blocks"]]  # type: ignore[attr-defined]
    assert kinds == ["fold", "rows", "fold"]
    noted = diff_props(
        {
            "before": BEFORE,
            "after": AFTER,
            "notes": [{"side": "after", "lines": 3, "note": "n"}],
        }
    )
    assert [b["header"] for b in noted["blocks"]][1] == "@@ -3 +3 @@"  # type: ignore[attr-defined]
    assert noted["notes"][0]["where"] == "after line 3"  # type: ignore[index]


def test_diff_split_flag_and_row_cap() -> None:
    assert diff_props({"before": "a", "after": "b", "mode": "split"})["split"] is True
    assert diff_props({"before": "a", "after": "b"})["split"] is False
    big = "".join(f"row {i}\n" for i in range(5100))
    blocks = diff_props({"before": "", "after": big})["blocks"]
    assert blocks[-1] == {"kind": "more", "header": "100", "rows": []}  # type: ignore[index]


def test_diff_rows_carry_highlighted_tokens() -> None:
    props = diff_props(
        {"language": "python", "before": "x = 1\n", "after": "x = 'a'  # c\n"}
    )
    rows = props["blocks"][0]["rows"]  # type: ignore[index]
    kinds = {kind for row in rows for kind, _ in row["code"]}
    assert {"s", "c"} <= kinds


# --- file-tree ---


def _tree_host(*paths: str) -> str:
    props = file_tree_props({"entries": [{"path": path} for path in paths]})
    return mount_block("file-tree", props, "src")


def test_file_tree_links_a_file_to_the_code_block_with_that_title() -> None:
    doc = (
        "```ui\n"
        'c = code(language: "py", title: "pkg/mod.py", source: "x = 1\\n")\n'
        'f = file-tree(entries: [{path: "src/pkg/mod.py"}, {path: "other.py"}])\n'
        "```\n"
    )
    body = render_page(doc, "t.md").body
    (tree,) = host_props(body, "file-tree")
    assert re.fullmatch(r"blk-[\w/-]+", tree["links"]["src/pkg/mod.py"])  # type: ignore[index]
    assert list(tree["links"]) == ["src/pkg/mod.py"]  # type: ignore[call-overload]


def test_file_tree_without_a_code_block_has_no_links() -> None:
    assert link_file_trees(_tree_host("a.py"), {}) == _tree_host("a.py")
    linked = link_file_trees(_tree_host("a/b.py"), {"b.py": "x"})
    assert host_props(linked, "file-tree")[0]["links"] == {"a/b.py": "blk-x"}


def test_code_titles_read_nested_hosts_and_skip_untitled_ones() -> None:
    titled = mount_block("code", code_props("x", "py", Panel(title="a.py")), "")
    plain = mount_block("code", code_props("x", "py"), "")
    assert code_titles(f"<div>{plain}{titled}</div>") == ["a.py"]


# --- change-summary ---


def test_change_summary_counts_the_pages_markers() -> None:
    doc = (
        "```ui\n"
        "s = change-summary()\n"
        'f = file-tree(entries: [{path: "a.py", change: "added"}])\n'
        "```\n"
    )
    (summary,) = host_props(render_page(doc, "t.md").body, "change-summary")
    assert summary["text"] == "1 file added"
    bare = "```ui\ns = change-summary()\n```\n"
    assert (
        host_props(render_page(bare, "t.md").body, "change-summary")[0]["text"] == EMPTY
    )
    assert change_summary_props({}, None)["text"] == UNCOUNTED


# --- deps ---


def _edges(text: str) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for line in text.splitlines():
        task, _, rest = line.partition(":")
        found.setdefault(task.strip(), []).extend(
            dep.strip() for dep in rest.split(",") if dep.strip()
        )
    return found


def test_deps_layout_marks_unknown_nodes_and_empty_graphs() -> None:
    assert deps_layout({}) == {"empty": True}
    layout = deps_layout(_edges("a: ghost"))
    nodes = {n["label"]: n for n in layout["nodes"]}  # type: ignore[attr-defined]
    assert nodes["ghost"]["known"] is False
    assert nodes["ghost"]["title"] == "ghost (not defined)"
    assert nodes["a"]["known"] is True


def test_deps_layout_draws_back_edges_and_clips_long_labels() -> None:
    cycle = deps_layout(_edges("a: b\nb: a\nc: c"))
    assert [e["back"] for e in cycle["edges"]].count(True) >= 1  # type: ignore[attr-defined]
    long = deps_layout(_edges("a-very-long-task-name-indeed:"))
    assert long["nodes"][0]["label"].endswith("…")  # type: ignore[index]


@pytest.mark.slow
def test_deps_layout_caps_nodes_and_edges() -> None:
    layout = deps_layout(_edges("a: " + ",".join(f"d{i}" for i in range(20000))))
    assert layout["truncated"] is True
    assert len(layout["nodes"]) <= 200 and len(layout["edges"]) <= 400  # type: ignore[arg-type]


def test_bundle_and_fixtures_stay_in_step() -> None:
    names = {path.stem for path in FIXTURES.glob("*.json")}
    assert set(BLOCKS) <= names


def test_hosts_carry_the_blocks_copy_text_before_mounting() -> None:
    doc = (
        "```ui\n"
        'c = code(language: "py", source: "a <b>\\nc\\n")\n'
        'f = file-tree(entries: [{path: "a/b.py"}])\n'
        's = change-summary(title: "T")\n'
        "```\n\n```py\nplain\n```\n"
    )
    body = render_page(doc, "t.md").body
    copies = re.findall(r'<div data-mithril="[\w-]+"[^>]*? data-copy="([^"]*)"', body)
    assert [html.unescape(c) for c in copies] == [
        "a <b>\nc",
        "1 file: 1 unchanged\na/b/\n  b.py".replace("a/b/\n  b.py", "a/\n  b.py"),
        "T\nNo changes marked on this page.",
        "plain",
    ]


def test_a_container_copies_the_held_codes_raw_text() -> None:
    doc = (
        "```ui\n"
        'c = code(language: "py", source: "queue.append(x)\\n")\n'
        't = tabs(tab: [{"label": "Code", "blocks": ["c"]}])\n'
        "```\n"
    )
    body = fill_containers(render_page(doc, "t.md").body)
    found = re.search(r'<div data-mithril="tabs"[^>]*data-copy="([^"]*)"', body)
    assert found and html.unescape(found[1]) == "Code\n\nqueue.append(x)"
