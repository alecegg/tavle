"""Standalone page commands."""

import argparse
import json
import sys
from pathlib import Path

from .listings import check_text_lines, comment_text, filtered_comments, finding_row
from .page.assemble import assemble_static, render_fragment
from .page.page_check import check
from .page.page_quality import quality_warnings
from .theme.layers import parse_toml
from .theme.tokens import ThemeError


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="tavle")
    commands = result.add_subparsers(dest="verb", required=True)
    for name in ("export", "render", "check", "comments"):
        command = commands.add_parser(name)
        command.add_argument("doc", type=Path)
        if name in ("export", "render"):
            command.add_argument("--theme", type=Path, action="append", default=[])
        if name == "export":
            command.add_argument("--out", type=Path, required=True)
        if name in ("check", "comments"):
            command.add_argument("--json", action="store_true")
        if name == "comments":
            command.add_argument("--open", action="store_true")
            command.add_argument("--kind")
    return result


def run(args: argparse.Namespace) -> int:
    args.doc.stat()
    if args.verb in ("export", "render"):
        layers = [
            (parse_toml(path.read_text(encoding="utf-8"), str(path)), str(path))
            for path in args.theme
        ]

        def theme_layers(_doc: Path):
            return layers

        if args.verb == "export":
            args.out.write_text(
                assemble_static(args.doc, theme_layers), encoding="utf-8"
            )
        else:
            print(render_fragment(args.doc, theme_layers))
        return 0
    if args.verb == "comments":
        rows = filtered_comments(args.doc, args.open, args.kind)
        print(
            json.dumps({"comments": rows})
            if args.json
            else "\n".join(map(comment_text, rows))
        )
        return 0
    text = args.doc.read_text(encoding="utf-8")
    errors = check(text, args.doc.parent)
    tasks = args.doc.parent / "tasks"
    task_ids = [path.stem for path in tasks.glob("*.md")]
    warnings = quality_warnings(text, task_ids)
    if args.json:
        print(
            json.dumps(
                {
                    "errors": [finding_row(e) for e in errors],
                    "warnings": [finding_row(w) for w in warnings],
                }
            )
        )
    else:
        print("\n".join(check_text_lines(args.doc, errors, warnings)))
    return int(bool(errors))


def main() -> int:
    args = parser().parse_args()
    try:
        return run(args)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 2
    except (OSError, UnicodeError, ThemeError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
