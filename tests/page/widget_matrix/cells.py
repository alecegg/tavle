"""Matrix axes and cell definitions (pure; no browser)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from itertools import combinations
from pathlib import Path

WIDTHS = (320, 375, 768, 1024, 1440)
SCHEMES = ("light", "dark")
MODES = (
    "default",
    "reduced-motion",
    "zoom200",
    "coarse",
    "forced-colors",
    "print",
    "nojs",
    "rtl",
)
FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "widgets"
WIDGETS = ("chrome", "choice", "form", "ranking", "slider", "decision", "comment")
WIDGET_FIXTURES = ("normal.md", "stress.md")
PAGE_FIXTURES = {
    "page-header.md": "page_header",
    "page-header-stress.md": "page_header",
}  # whole-page chrome, no blocks
# Viewport breakpoints sit at 24, 30 and 40 rem (384, 480, 641 px); the vd-doc container
# (viewport minus 2 rem) has breakpoints at 28, 36, 44 and 64 rem. So 375 shares 320's
# band (21.4 rem container) and 1024 shares 768's (62 rem, in the 44-64 rem band).
# Every mode keeps one width per band with a sample; default mode keeps all five.
OTHER_MODE_WIDTHS = (320, 768, 1440)
WALK_MODES = ("default", "reduced-motion", "zoom200", "coarse", "nojs", "rtl")


@dataclass(frozen=True)
class Cell:
    family: str
    fixture: str
    width: int
    scheme: str
    mode: str

    @property
    def id(self) -> str:
        stem = self.fixture.removesuffix(".md")
        return f"{self.family}-{stem}-w{self.width}-{self.scheme}-{self.mode}"

    @property
    def in_subset(self) -> bool:
        """Whether this page belongs to the pairwise default run."""
        return self.page_key in selected_keys()

    @property
    def page_key(self) -> tuple[str, int, str, str]:
        return (self.fixture, self.width, self.scheme, self.mode)


def widths_for(mode: str) -> tuple[int, ...]:
    return WIDTHS if mode == "default" else OTHER_MODE_WIDTHS


def rich_family(fixture: str) -> str | None:
    """`rich-chart.md` and `rich-chart-stress.md` hold family `rich-chart`."""
    stem = fixture.removesuffix(".md").removesuffix("-stress")
    return stem if stem.startswith("rich-") else None


def families_in(fixture: str) -> tuple[str, ...]:
    rich = rich_family(fixture)
    if fixture in PAGE_FIXTURES:
        return (PAGE_FIXTURES[fixture],)
    return (rich,) if rich else WIDGETS


def scope_for(family: str) -> dict[str, str | None]:
    """Selector scope the audit runs in: chrome is everything outside `.vb`."""
    if family in ("chrome", *PAGE_FIXTURES.values()):
        return {"inside": None, "outside": ".vb"}
    if family.startswith("rich-"):
        return {"inside": ".vb", "outside": None}
    return {"inside": f".vb.{family}", "outside": None}


def fixture_names(directory: Path = FIXTURES) -> tuple[str, ...]:
    rich = sorted(p.name for p in directory.glob("rich-*.md"))
    return (*WIDGET_FIXTURES, *PAGE_FIXTURES, *rich)


def all_cells(directory: Path = FIXTURES) -> list[Cell]:
    return [
        Cell(family, fixture, width, scheme, mode)
        for fixture in fixture_names(directory)
        for family in families_in(fixture)
        for mode in MODES
        for width in widths_for(mode)
        for scheme in SCHEMES
    ]


PageKey = tuple[str, int, str, str]
Requirement = tuple[object, ...]


@cache
def _coverage() -> dict[PageKey, frozenset[Requirement]]:
    coverage: dict[PageKey, set[Requirement]] = {}
    for cell in all_cells():
        requirements = coverage.setdefault(cell.page_key, set())
        requirements.add(("fixture", cell.fixture))
        axes = (
            ("family", cell.family),
            ("width", cell.width),
            ("scheme", cell.scheme),
            ("mode", cell.mode),
        )
        requirements.update(combinations(axes, 2))
    return {key: frozenset(value) for key, value in coverage.items()}


def uncovered(keys: set[PageKey] | frozenset[PageKey]) -> set[Requirement]:
    """Return valid axis pairs and fixtures absent from the selected pages."""
    coverage = _coverage()
    required = set().union(*coverage.values())
    for key in keys:
        required.difference_update(coverage[key])
    return required


@cache
def selected_keys() -> frozenset[PageKey]:
    """Greedily cover requirements, resolving ties by sorted page key."""
    coverage = _coverage()
    remaining = uncovered(frozenset())
    selected: set[PageKey] = set()
    while remaining:
        key = min(coverage, key=lambda k: (-len(coverage[k] & remaining), k))
        selected.add(key)
        remaining.difference_update(coverage[key])
    return frozenset(selected)
