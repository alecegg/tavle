"""Standalone page commands."""

import argparse
import json
import sys
import webbrowser
from pathlib import Path

from .listings import (
    check_text_lines,
    comment_text,
    filtered_comments,
    finding_row,
    parse_port,
)
from .page.assemble import assemble_static, render_fragment
from .page.page_quality import check_doc
from .serve.netbind import LOOPBACK
from .serve.serve import serve
from .theme.layers import parse_toml
from .theme.tokens import ThemeError


def serve_options(command: argparse.ArgumentParser) -> None:
    command.add_argument("--port", type=parse_port, default=0)
    command.add_argument("--host", default=LOOPBACK)
    command.add_argument("--allow-edit", action="store_true")
    command.add_argument("--open", action="store_true")


def listing_options(command: argparse.ArgumentParser, name: str) -> None:
    if name in ("check", "comments"):
        command.add_argument("--json", action="store_true")
    if name == "comments":
        command.add_argument("--open", action="store_true")
        command.add_argument("--kind")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="tavle")
    commands = result.add_subparsers(dest="verb", required=True)
    for name in ("export", "render", "serve", "check", "comments"):
        command = commands.add_parser(name)
        command.add_argument("doc", type=Path)
        if name in ("export", "render", "serve"):
            command.add_argument("--theme", type=Path, action="append", default=[])
        if name == "serve":
            serve_options(command)
        if name == "export":
            command.add_argument("--out", type=Path, required=True)
        listing_options(command, name)
    return result


def run(args: argparse.Namespace) -> int:
    args.doc.stat()
    if args.verb in ("export", "render", "serve"):

        def theme_layers(_doc: Path):
            return [
                (parse_toml(path.read_text(encoding="utf-8"), str(path)), str(path))
                for path in args.theme
            ]

        if args.verb == "serve":

            def ready(url: str) -> None:
                print(url, flush=True)
                if args.open:
                    webbrowser.open(url)

            serve(args.doc, args.port, ready, args.host, args.allow_edit, theme_layers)
            return 0

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
    errors, warnings = check_doc(args.doc)
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
