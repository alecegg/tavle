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


class FenceScanner:
    """Track fence lines using the calling parser's established closing policy."""

    def __init__(self, policy: str = "render") -> None:
        self.policy = policy
        self.opening: re.Match[str] | None = None
        self.start = 0

    def feed(self, line: str, number: int = 0, *, allow_open: bool = True) -> bool:
        """Return whether this line is a fence marker, updating the open fence."""
        match = FENCE.match(line)
        if match is None:
            return False
        if self.opening is None:
            if allow_open:
                self.opening, self.start = match, number
        elif self._closes(line, match, self.opening):
            self.opening = None
        return True

    def _closes(
        self, line: str, match: re.Match[str], opening_match: re.Match[str]
    ) -> bool:
        opening = opening_match.group(2)
        marker = match.group(2)
        same = marker[0] == opening[0]
        if self.policy == "words":
            return same
        if self.policy == "markers":
            return same and len(marker) >= len(opening)
        closes = fence_closes(line, opening_match)
        if self.policy == "strict":
            closes = closes and not match.group(4).strip()
        return closes
