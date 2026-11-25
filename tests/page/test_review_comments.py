from __future__ import annotations

from pathlib import Path

import pytest

from tavle import (
    append_comment,
    append_status,
    comments_path,
    fold,
    read_rows,
    target_anchor,
)

LINE = {
    "kind": "line",
    "file": "src/a.py",
    "line": 12,
    "side": "new",
    "sha": "abcdef123456",
}


def _post(doc: Path, target: dict | None = None, **extra: object) -> dict:
    if target is not None:
        extra["target"] = target
    anchor = target_anchor(target) if target else "p1"
    return append_comment(doc, anchor, "q", "text", extra=extra)


def test_bad_target_rejected(tmp_path: Path) -> None:
    doc = tmp_path / "r.json"
    bad = {"kind": "line", "line": 12, "side": "new", "sha": "abc"}
    with pytest.raises(ValueError):
        append_comment(doc, "line-abc-12", "q", "t", extra={"target": bad})
    with pytest.raises(ValueError):
        append_comment(doc, "report", "q", "t", extra={"review_kind": "bogus"})
    assert not comments_path(doc).exists()


def test_line_comment(tmp_path: Path) -> None:
    row = _post(tmp_path / "r.json", LINE)
    assert row["target"] == LINE
    assert row["anchor"] == "line-abcdef1-12"


def test_target_survives_fold(tmp_path: Path) -> None:
    doc = tmp_path / "r.json"
    _post(doc, LINE, review_kind="question")
    [comment] = fold(read_rows(doc))
    assert comment["target"] == LINE
    assert comment["review_kind"] == "question"
    assert comment["kind"] == "comment"


def test_fix_this(tmp_path: Path) -> None:
    doc = tmp_path / "r.json"
    target = {"kind": "finding", "id": "0123456789abcdef"}
    row = append_comment(
        doc,
        target_anchor(target),
        "",
        "add a guard",
        extra={"target": target, "review_kind": "fix"},
    )
    assert row["anchor"] == "finding-0123456789abcdef"
    [comment] = fold(read_rows(doc))
    assert comment["review_kind"] == "fix"
    assert comment["text"] == "add a guard"


def test_legacy_rows_unchanged(tmp_path: Path) -> None:
    doc = tmp_path / "r.json"
    append_comment(doc, "p1", "q", "hello")
    [comment] = fold(read_rows(doc))
    assert not {"target", "review_kind", "status"} & comment.keys()
    assert comment["replies"] == []


def test_fixed(tmp_path: Path) -> None:
    doc = tmp_path / "r.json"
    cid = _post(doc)["id"]
    append_status(doc, cid, "fixed", "guard added")
    [comment] = fold(read_rows(doc))
    assert comment["status"] == "fixed"
    assert comment["replies"][0]["text"] == "guard added"
    assert comment["replies"][0]["status"] == "fixed"


def test_status_without_note(tmp_path: Path) -> None:
    doc = tmp_path / "r.json"
    cid = _post(doc)["id"]
    append_status(doc, cid, "working")
    [comment] = fold(read_rows(doc))
    assert comment["status"] == "working"
    assert comment["replies"][0]["text"] == "working"


def test_unknown_comment(tmp_path: Path) -> None:
    doc = tmp_path / "r.json"
    with pytest.raises(ValueError):
        append_status(doc, "cnope", "fixed")
    assert not comments_path(doc).exists()
    cid = _post(doc)["id"]
    with pytest.raises(ValueError):
        append_status(doc, cid, "bogus")


def test_working_does_not_resolve(tmp_path: Path) -> None:
    doc = tmp_path / "r.json"
    cid = _post(doc)["id"]
    append_status(doc, cid, "working")
    [comment] = fold(read_rows(doc))
    assert comment["state"] == "open"


def test_line_target_sha_must_be_hex(tmp_path: Path) -> None:
    doc = tmp_path / "r.json"
    for sha in ("--output=x", "--outpu", "zzzzzzz", "abc123"):
        bad = {**LINE, "sha": sha}
        with pytest.raises(ValueError):
            append_comment(doc, "line-abcdef1-12", "q", "t", extra={"target": bad})
    assert not comments_path(doc).exists()


def test_target_anchor_slugs_ids_with_capitals_and_keeps_the_stored_target():
    target = {"kind": "finding", "id": "R2"}
    anchor = target_anchor(target)
    assert anchor == "finding-r2"
    assert target_anchor({"kind": "section", "id": "A b_C"}) == "section-a-b-c"


def test_block_target_is_stored_and_anchors_like_a_section(tmp_path: Path) -> None:
    doc = tmp_path / "r.json"
    target = {"kind": "block", "id": "checkout-flow"}
    assert target_anchor(target) == "block-checkout-flow"
    assert target_anchor({"kind": "block", "id": "A b_C"}) == "block-a-b-c"
    append_comment(doc, "block-checkout-flow", "q", "t", extra={"target": target})
    assert '"kind":"block"' in comments_path(doc).read_text()


def test_block_target_requires_an_id(tmp_path: Path) -> None:
    doc = tmp_path / "r.json"
    with pytest.raises(ValueError):
        append_comment(doc, "block-x", "q", "t", extra={"target": {"kind": "block"}})
    assert not comments_path(doc).exists()
