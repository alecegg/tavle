"""Pure listings and formatting for page commands."""

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .blocks.check import BlockError
from .blocks.reference import catalog
from .comments.answers import answer_schema
from .comments.comments import fold, mark_latest_decisions, one_line, read_rows
from .page import page_check


def parse_port(text: str) -> int:
    """Return a TCP port 0-65535; raise ValueError otherwise."""
    if not text.isascii() or not text.isdigit() or int(text) > 65535:
        raise ValueError(f"bad port {text!r}: use an integer 0-65535")
    return int(text)


def comment_head(comment: dict[str, Any]) -> str:
    if comment.get("kind") == "decision":
        latest = " latest" if comment.get("latest") else ""
        return (
            f"{comment['id']} decision {comment.get('state', '')} "
            f"{comment.get('item', '')} {comment.get('verdict', '')}{latest} "
            f"{comment.get('ts', '')}"
        )
    return (
        f"{comment['id']} {comment.get('kind', 'comment')} "
        f"{comment.get('state', '')} {comment.get('anchor', '')}"
    )


def comment_text(comment: dict[str, Any]) -> str:
    head = one_line(comment_head(comment))
    parts = [head, f"  {one_line(comment.get('text', ''))}"]
    parts.extend(
        f"  reply {one_line(reply.get('actor', ''))}: {one_line(reply.get('text', ''))}"
        for reply in comment.get("replies", [])
    )
    return "\n".join(parts)


def filtered_comments(
    doc: Path, open_only: bool, kind: str | None
) -> list[dict[str, Any]]:
    rows = mark_latest_decisions(fold(read_rows(doc)))
    rows = [c for c in rows if not open_only or c["state"] == "open"]
    return [c for c in rows if kind is None or c.get("kind") == kind]


def block_types() -> tuple[str, ...]:
    return tuple(sorted(page_check.PAGE_SPECS))


def _with_answer_schema(row: dict[str, object]) -> dict[str, object]:
    """The catalog row plus the answer schema its example takes (None if none)."""
    example = page_check.PAGE_SPECS[str(row["name"])].example
    item = example.split("=", 1)[0].strip()
    schema = answer_schema(f"```ui\n{example}```\n", item)
    return {**row, "answer_schema": asdict(schema) if schema else None}


def finding_row(finding: BlockError) -> dict[str, object]:
    return {
        "code": finding.rule,
        "line": finding.line,
        "statement_id": finding.statement_id,
        "path": finding.path,
        "message": finding.message,
    }


def check_result(
    errors: list[BlockError], warnings: list[BlockError]
) -> dict[str, list[dict[str, object]]]:
    return {
        "errors": [finding_row(e) for e in errors],
        "warnings": [finding_row(w) for w in warnings],
    }


def block_rows(name: str | None) -> list[dict[str, object]]:
    return [
        _with_answer_schema(row)
        for row in catalog(page_check.PAGE_SPECS, (name,) if name else ())
    ]


def check_text_lines(
    doc: Path, errors: list[BlockError], warnings: list[BlockError]
) -> list[str]:
    return [f"{doc}:{e.line}: {e.rule}: {e.message}" for e in errors] + [
        f"{doc}:{w.line}: warning: {w.rule}: {w.message}" for w in warnings
    ]
