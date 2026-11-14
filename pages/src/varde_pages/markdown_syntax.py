"""Markdown fence and heading syntax shared by the page parser and renderer."""

from __future__ import annotations

import hashlib
import re

FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*([\w-]*)(.*)")
HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")


def slugify(text: str) -> str:
    plain = re.sub(r"[`*_]", "", text).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", plain).strip("-")
    if slug:
        return slug
    return "section-" + hashlib.sha256(plain.encode("utf-8")).hexdigest()[:6]


def fence_closes(line: str, opening: re.Match[str]) -> bool:
    """Whether `line` closes the fence `opening` matched."""
    closing = FENCE.match(line)
    return bool(
        closing
        and closing.group(2)[0] == opening.group(2)[0]
        and len(closing.group(2)) >= len(opening.group(2))
        and not closing.group(3)
    )
