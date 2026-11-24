"""The file-tree block: folding, order, renames, faults, escaping and code links."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from varde.pages.page_check import PAGE_SPECS
from varde.ui.blocks import check_props, type_text
from varde.ui.blocks_render.file_tree import (
    compact,
    fold,
    match_target,
    summary_text,
)

FIXTURES = Path(__file__).parent / "fixtures" / "widgets"
HOSTILE = '<img src=x onerror=alert(1)> "q" &amp; <script>alert(1)</script>'


def tree(*entries: dict[str, Any], **extra: object) -> dict[str, object]:
    return {"entries": list(entries), **extra}


def rules(data: dict[str, object]) -> list[str]:
    return [e.rule for e in check_props("file-tree", data, 1)]


def test_fold_nests_paths_and_orders_folders_before_files() -> None:
    root = fold(
        [{"path": "b.py"}, {"path": "z/x.py"}, {"path": "a/y.py"}, {"path": "A.py"}]
    )
    assert sorted(root.folders) == ["a", "z"]
    assert sorted(root.files) == ["A.py", "b.py"]
    assert root.count() == 4


def test_single_child_chain_is_compacted() -> None:
    root = fold([{"path": "a/b/c/d.py"}, {"path": "a/b/c/e.py"}])
    shown = compact(root.folders["a"])
    assert (shown.name, shown.path) == ("a/b/c", "a/b/c")
    assert list(shown.files) == ["d.py", "e.py"]


def test_duplicate_path_is_a_fault() -> None:
    data = tree({"path": "a/b.py"}, {"path": "a/b.py"})
    assert "duplicate-path" in rules(data)
    with pytest.raises(ValueError):
        fold(data["entries"])  # type: ignore[arg-type]


def test_file_and_folder_clash_is_a_fault() -> None:
    assert "path" in rules(tree({"path": "a"}, {"path": "a/b.py"}))


@pytest.mark.parametrize("path", ["/a.py", "a//b.py", "a/", "a/../b.py", "./a.py", ""])
def test_bad_paths_are_faults(path: str) -> None:
    assert rules(tree({"path": path}))


def test_props_are_validated() -> None:
    assert rules(tree({"path": "a.py"}, collapse=2, title="t")) == []
    assert rules(tree({"path": "a.py"}, collapse=-1))
    assert rules(tree({"path": "a.py"}, collapse=True))
    assert rules(tree({"path": "a.py", "change": "bogus"}))
    assert rules(tree({"path": "a.py", "change": "renamed"}))  # needs was
    assert rules(tree({"path": "a.py", "extra": 1}))
    assert rules({"entries": []})


def test_summary_counts_equal_entries() -> None:
    entries = [
        {"path": "a", "change": "added"},
        {"path": "b", "change": "added"},
        {"path": "c", "change": "removed"},
        {"path": "d"},
    ]
    assert summary_text(entries) == "4 files: 2 added, 1 removed, 1 unchanged"
    assert summary_text(entries[:1]) == "1 file: 1 added"


def test_match_target_prefers_the_exact_then_the_longest_tail() -> None:
    titles = {"queue.py": "top/1", "src/queue.py": "top/2", "x.py": "top/3"}
    assert match_target("src/queue.py", titles) == "top/2"
    assert match_target("lib/src/queue.py", titles) == "top/2"
    assert match_target("lib/queue.py", titles) == "top/1"
    assert match_target("src/equeue.py", titles) == ""


def test_help_text_lists_the_props() -> None:
    text = type_text(PAGE_SPECS, "file-tree")
    assert text.startswith("file-tree - ") and "collapse" in text and "entries" in text
