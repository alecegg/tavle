"""Matrix axes and cell definitions (pure; no browser)."""

from __future__ import annotations

from dataclasses import dataclass
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
SUBSET_DEFAULT_WIDTHS = (320, 1440)
SUBSET_MODE_WIDTH = 320
SUBSET_MODE_SCHEME = "light"
# Rich blocks share one stylesheet, so the subset runs them in three modes only.
SUBSET_RICH_MODES = ("default", "coarse", "nojs", "rtl")
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
        """Per-change run: two default widths, one width for other modes."""
        if self.mode == "default":
            return self.width in SUBSET_DEFAULT_WIDTHS
        if rich_family(self.fixture) and self.mode not in SUBSET_RICH_MODES:
            return False
        return self.width == SUBSET_MODE_WIDTH and self.scheme == SUBSET_MODE_SCHEME

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
