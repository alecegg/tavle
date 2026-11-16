"""Anchor assignment and source digests shared by renderers and source readers."""

import hashlib
from collections.abc import Collection

from varde_pages.markdown_syntax import slugify


def block_hash(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]


def unique_anchor(slug: str, seen: dict[str, int], taken: set[str]) -> str:
    """Return slug, or slug-N for the first unused N, and record it as used."""
    candidate = slug
    while candidate in seen or candidate in taken:
        seen[slug] = seen.get(slug, 1) + 1
        candidate = f"{slug}-{seen[slug]}"
    seen.setdefault(candidate, 1)
    return candidate


def unique_id_anchor(
    block_id: str, taken: set[str], reserved: Collection[str] = ()
) -> str:
    """The id, or id-N for the first N used by no anchor and no other statement id."""
    candidate, n = block_id, 1
    while candidate in taken or (n > 1 and candidate in reserved):
        n += 1
        candidate = f"{block_id}-{n}"
    return candidate


class AnchorState:
    def __init__(self, reserved: Collection[str] = (), *, reserve_ids: bool = True):
        self.reserved = set(reserved)
        self.reserve_ids = reserve_ids
        self.seen: dict[str, int] = {}
        self.taken: set[str] = set()

    def place(
        self,
        kind: str,
        text: str,
        block_id: str | None,
        section: str,
        count: int,
        explicit_id: str | None = None,
    ) -> tuple[str, str, int]:
        if kind == "heading":
            if explicit_id:
                section = unique_id_anchor(explicit_id, self.taken)
            else:
                section = unique_anchor(
                    slugify(text), self.seen, self.taken | self.reserved
                )
            anchor, count = section, 0
        else:
            count += 1
            reserved = self.reserved if self.reserve_ids else ()
            anchor = (
                unique_id_anchor(block_id, self.taken, reserved)
                if block_id
                else f"{section}/{count}"
            )
        self.taken.add(anchor)
        return anchor, section, count
