"""Find typed block fences in markdown text. Pure; no TOML here."""

import re
from collections.abc import Iterator
from dataclasses import dataclass

from varde_data.ui_lines import ParseResult, Statement, parse_lines

from varde_pages.markdown_syntax import FENCE, FenceScanner

_ID_WORD = re.compile(r"^id=(.*)$")


@dataclass(frozen=True)
class Fence:
    lang: str
    line: int  # 1-based document line of the opening fence
    id_text: str | None  # raw value of the first `id=` word, if any
    body: str  # dedented body; body line k is document line `line + k`


def _id_text(info_rest: str) -> str | None:
    for word in info_rest.split():
        match = _ID_WORD.match(word)
        if match:
            return match.group(1)
    return None


@dataclass(frozen=True)
class FenceSpan:
    start: int  # 0-based index of the opening line
    end: int | None  # index of the closing line; None when never closed
    lang: str
    marker: str  # the backtick or tilde run
    indent: int  # columns of leading whitespace on the opening line
    info: str  # opening line text after the language word
    id_text: str | None


def dedent_lines(lines: list[str], indent: int) -> list[str]:
    """Remove up to `indent` characters of leading whitespace from each line."""
    return [ln[min(indent, len(ln) - len(ln.lstrip())) :] for ln in lines]


def scan_fences(lines: list[str]) -> list[FenceSpan]:
    """Top-level fences of tab-expanded lines (no line ends), in document order."""
    spans: list[FenceSpan] = []
    i = 0
    while i < len(lines):
        opening = FENCE.match(lines[i])
        if opening is None:
            i += 1
            continue
        indent, marker, lang = len(opening.group(1)), opening.group(2), opening.group(3)
        j = i + 1
        scanner = FenceScanner("strict")
        scanner.feed(lines[i])
        while j < len(lines):
            scanner.feed(lines[j])
            if scanner.opening is None:
                break
            j += 1
        end = j if j < len(lines) else None
        info = opening.group(4)
        spans.append(FenceSpan(i, end, lang, marker, indent, info, _id_text(info)))
        i = j + 1
    return spans


def find_fences(text: str, langs: frozenset[str]) -> list[Fence]:
    """Return every fence whose language is in langs, in document order."""
    lines = text.expandtabs(4).splitlines()
    return [
        Fence(
            span.lang,
            span.start + 1,
            span.id_text,
            "\n".join(
                dedent_lines(
                    lines[span.start + 1 : span.end or len(lines)], span.indent
                )
            ),
        )
        for span in scan_fences(lines)
        if span.lang in langs
    ]


def ui_results(text: str) -> Iterator[tuple[int, ParseResult]]:
    """`(document line of the fence, parse result)` for each `ui` fence, in order."""
    for fence in find_fences(text, frozenset({"ui"})):
        yield fence.line, parse_lines(fence.body)


def ui_statements(text: str) -> Iterator[tuple[int, Statement]]:
    """Each `ui` statement of the page with its 1-based document line."""
    for fence_line, result in ui_results(text):
        for statement in result.statements:
            yield fence_line + statement.line, statement
