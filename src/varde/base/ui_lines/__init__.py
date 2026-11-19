"""Line syntax for page components: grammar and pure parser."""

from varde.base.ui_lines.parse import (
    ParseError,
    ParseResult,
    Ref,
    Statement,
    parse_lines,
)

__all__ = ["ParseError", "ParseResult", "Ref", "Statement", "parse_lines"]
