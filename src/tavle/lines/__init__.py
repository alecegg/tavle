"""Line syntax for page components: grammar and pure parser."""

from varde.ui.lines.parse import (
    ParseError,
    ParseResult,
    Ref,
    Statement,
    parse_lines,
)

__all__ = ["ParseError", "ParseResult", "Ref", "Statement", "parse_lines"]
