"""Append-only comment log for an interactive doc page: store, fold, reply."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import secrets
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from varde_pages.include import IncludeSource, read_source_text
from varde_pages.select import read_source
from varde_pages.validation import CONTROLS

_KEPT_KEYS = (
    "id", "ts", "anchor", "quote", "text", "state", "actor",
    "replacement", "item", "verdict", "value", "target", "review_kind", "status",
)  # fmt: skip
KINDS = ("comment", "suggestion", "drift", "decision", "answer")
ANSWER_KINDS = ("decision", "answer")  # a `decision` row is read as an answer
REVIEW_KINDS = ("fix", "question", "nit", "decide")
STATUSES = ("working", "fixed", "answered", "wontfix", "noted")
_TARGET_FIELDS = {
    "line": ("file", "line", "side", "sha"),
    "finding": ("id",),
    "candidate": ("key",),
    "section": ("id",),
    "block": ("id",),
    "report": (),
}
_ANCHOR = re.compile(r"[a-z0-9-]+(/[0-9]+)?")
_SHA = re.compile(r"[0-9a-fA-F]{7,64}")
_INTERVAL = re.compile(r"(\d+)([sm])")


def one_line(value: object) -> str:
    """Text for one terminal line: controls replaced, whitespace collapsed."""
    return " ".join(CONTROLS.sub(" ", str(value)).split())


def comments_path(doc: Path) -> Path:
    """The comments log of `doc`, beside it."""
    return doc.with_name(doc.name + ".comments.jsonl")


def parse_interval(text: str) -> float:
    """Return seconds for `<N>s` or `<N>m`; raise ValueError otherwise."""
    match = _INTERVAL.fullmatch(text.strip())
    if match is None or int(match.group(1)) == 0:
        raise ValueError(f"bad interval {text!r}: use <N>s or <N>m, N > 0")
    return int(match.group(1)) * (60 if match.group(2) == "m" else 1)


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _append_row(path: Path, row: dict[str, Any]) -> None:
    """One `O_APPEND` write of one line; refuses a symlinked log.

    A log whose last byte is not a newline (a torn earlier write) gets a leading
    newline inside the same write, decided from the descriptor itself under an
    exclusive `flock`, so a concurrent writer's partial append is never read.
    """
    encoded = (
        json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_APPEND | os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as error:
        raise ValueError(f"cannot write {path.name}: not a regular file") from error
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)  # released on close
        size = os.fstat(descriptor).st_size
        if size and os.pread(descriptor, 1, size - 1) != b"\n":
            encoded = b"\n" + encoded
        if os.write(descriptor, encoded) != len(encoded):
            raise OSError("incomplete comment append")
    finally:
        os.close(descriptor)


def _check_target(target: object) -> None:
    """Raise ValueError unless `target` is a known kind with its fields."""
    if not isinstance(target, dict) or target.get("kind") not in _TARGET_FIELDS:
        raise ValueError(f"bad target {target!r}")
    for field in _TARGET_FIELDS[target["kind"]]:
        value = target.get(field)
        if value in (None, "") or isinstance(value, bool):
            raise ValueError(f"target {target['kind']!r} needs {field!r}")
    line = target.get("line")
    if target["kind"] == "line" and not isinstance(line, int):
        raise ValueError("target 'line' needs an integer 'line'")
    if target["kind"] == "line" and _SHA.fullmatch(str(target["sha"])) is None:
        raise ValueError("target 'line' needs a 7-64 character hex 'sha'")


def anchor_slug(value: object) -> str:
    """Lower-case `value`; every character outside `[a-z0-9-]` becomes `-`."""
    return re.sub(r"[^a-z0-9-]", "-", str(value).lower())


def target_anchor(target: dict[str, Any]) -> str:
    """The slug anchor of a valid target; it always matches `_ANCHOR`."""
    _check_target(target)
    kind = target["kind"]
    if kind == "line":
        return f"line-{str(target['sha'])[:7].lower()}-{target['line']}"
    if kind == "candidate":
        digest = hashlib.sha1(str(target["key"]).encode()).hexdigest()  # noqa: S324
        return f"candidate-{digest[:12]}"
    if kind == "report":
        return "report"
    return f"{kind}-{anchor_slug(target['id'])}"


def _check_extra(extra: dict[str, Any]) -> None:
    if "target" in extra:
        _check_target(extra["target"])
    if "review_kind" in extra and extra["review_kind"] not in REVIEW_KINDS:
        raise ValueError(f"bad review_kind {extra['review_kind']!r}")


def append_comment(
    doc: Path,
    anchor: str,
    quote: str,
    text: str,
    actor: str = "user",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append a comment row; `extra` carries kind, replacement, item, verdict."""
    if _ANCHOR.fullmatch(anchor) is None:
        raise ValueError(f"bad anchor {anchor!r}")
    if not text.strip():
        raise ValueError("empty comment text")
    _check_extra(extra or {})
    row = {
        "id": "c" + secrets.token_hex(8),
        "ts": _now(),
        "anchor": anchor,
        "quote": quote,
        "text": text,
        "state": "open",
        "actor": actor,
        **(extra or {}),
    }
    _append_row(comments_path(doc), row)
    return row


def mark_applied(doc: Path, comment_id: str, actor: str) -> None:
    """Resolve a suggestion and record who applied it."""
    row = {
        "id": comment_id,
        "ts": _now(),
        "state": "resolved",
        "applied_by": actor,
    }
    _append_row(comments_path(doc), row)


def append_reply(
    doc: Path,
    comment_id: str,
    text: str,
    actor: str = "agent",
) -> dict[str, Any]:
    if not any(c["id"] == comment_id for c in fold(read_rows(doc))):
        raise ValueError(f"unknown comment id {comment_id!r}")
    row = {
        "id": "r" + secrets.token_hex(4),
        "reply_to": comment_id,
        "ts": _now(),
        "text": text,
        "actor": actor,
    }
    path = comments_path(doc)
    _append_row(path, row)
    resolved = {"id": comment_id, "ts": row["ts"], "state": "resolved"}
    _append_row(path, resolved)
    return row


def append_status(
    doc: Path,
    comment_id: str,
    status: str,
    note: str = "",
    actor: str = "agent",
) -> dict[str, Any]:
    """Append a status reply; the parent stays as it is (not resolved)."""
    if status not in STATUSES:
        raise ValueError(f"bad status {status!r}: use one of {', '.join(STATUSES)}")
    if not any(c["id"] == comment_id for c in fold(read_rows(doc))):
        raise ValueError(f"unknown comment id {comment_id!r}")
    row = {
        "id": "r" + secrets.token_hex(4),
        "reply_to": comment_id,
        "ts": _now(),
        "text": note.strip() or status,
        "status": status,
        "actor": actor,
    }
    _append_row(comments_path(doc), row)
    return row


def mark_latest_decisions(comments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Copy answer rows, flagging `latest` on the newest answer per block id."""
    newest: dict[str, str] = {}
    for row in comments:
        if row.get("kind") in ANSWER_KINDS and isinstance(row.get("item"), str):
            newest[row["item"]] = row["id"]
    return [
        {**row, "latest": newest.get(row.get("item", "")) == row["id"]}
        if row.get("kind") in ANSWER_KINDS
        else row
        for row in comments
    ]


def read_rows(doc: Path) -> list[dict[str, Any]]:
    """Parse the log, skipping bad lines; a missing log is empty."""
    try:
        text = comments_path(doc).read_text(encoding="utf-8")
    except OSError, UnicodeError:
        return []
    rows = []
    for line in text.split("\n"):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError, TypeError:
            continue
        if isinstance(row, dict) and isinstance(row.get("id"), str):
            rows.append(row)
    return rows


def _reply_entry(row: dict[str, Any]) -> dict[str, Any]:
    return {k: row[k] for k in ("id", "ts", "text", "actor", "status") if k in row}


def _new_comment(row: dict[str, Any]) -> dict[str, Any]:
    comment = {k: row[k] for k in _KEPT_KEYS if k in row}
    kind = row.get("kind")
    comment["kind"] = kind if kind in KINDS else "comment"
    comment["replies"] = []
    return comment


def _fold_row(comments: dict[str, dict[str, Any]], row: dict[str, Any]) -> None:
    cid = row["id"]
    parent = row.get("reply_to")
    if isinstance(parent, str):
        if parent in comments and isinstance(row.get("text"), str):
            comments[parent]["replies"].append(_reply_entry(row))
            if row.get("status") in STATUSES:
                comments[parent]["status"] = row["status"]
    elif row.get("state") in {"open", "resolved"} and cid in comments:
        comments[cid]["state"] = row["state"]
        if isinstance(row.get("applied_by"), str):
            comments[cid]["applied_by"] = row["applied_by"]
    elif row.get("state") == "open" and isinstance(row.get("text"), str):
        comments[cid] = _new_comment(row)


def fold(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fold rows into comments; later state rows and replies attach by id."""
    comments: dict[str, dict[str, Any]] = {}
    for row in rows:
        _fold_row(comments, row)
    return list(comments.values())


# --- comments on included parts ------------------------------------------------


def source_anchors(source: IncludeSource) -> tuple[frozenset[str], frozenset[str]]:
    """Anchors inside the include's selected region, and every anchor of the source.

    The source is re-read and re-parsed, so a comment can only land on a block
    that exists now; raises ValueError when the source cannot be read.
    """
    blocks = read_source(read_source_text(source.path)).blocks
    inside = frozenset(
        b.anchor for b in blocks if b.start >= source.start and b.end <= source.end
    )
    return inside, frozenset(b.anchor for b in blocks)


def source_comments(source: IncludeSource, part: str) -> list[dict[str, Any]]:
    """Folded comments of a source's sidecar that belong to the include `part`.

    Rows anchored inside the selected region are kept; rows whose anchor no
    longer exists anywhere in the source are kept and flagged `orphaned`; rows
    on other parts of the source are left to the pages that include them.
    """
    if comments_path(source.path).is_symlink():
        return []
    try:
        inside, every = source_anchors(source)
    except ValueError:
        return []
    kept = []
    for comment in fold(read_rows(source.path)):
        if comment.get("kind") != "comment":
            continue  # answers, drift and suggestions belong to the source page
        anchor = comment.get("anchor", "")
        if anchor in inside:
            kept.append({**comment, "part": part})
        elif anchor not in every:
            kept.append({**comment, "part": part, "orphaned": True})
    return kept


def fold_with_sources(
    doc: Path, sources: Mapping[str, IncludeSource]
) -> list[dict[str, Any]]:
    """The page's own comments plus those of every included source part."""
    merged = fold(read_rows(doc))
    for part, source in sources.items():
        merged += source_comments(source, part)
    return merged


def append_part_comment(
    source: IncludeSource,
    anchor: str,
    quote: str,
    text: str,
    actor: str = "user",
) -> dict[str, Any]:
    """Append a comment to a source's sidecar; ValueError unless it is safe.

    The anchor must be inside the include's selected region of the source as it
    is now. The sidecar must sit beside the source (no redirected directory) and
    must not be a symlink; `_append_row` opens it with `O_NOFOLLOW`.
    """
    path = comments_path(source.path)
    try:
        moved = source.path.resolve(strict=True) != source.path
        redirected = path.parent.resolve(strict=True) != source.path.parent
    except OSError as error:
        raise ValueError("include source moved or changed") from error
    if moved or redirected or path.is_symlink():
        raise ValueError("comment log of the include source is not writable")
    if anchor not in source_anchors(source)[0]:
        raise ValueError(f"anchor {anchor!r} is outside the included part")
    return append_comment(source.path, anchor, quote, text, actor)
