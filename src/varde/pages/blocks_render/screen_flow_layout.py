"""Pure layout for the screen-flow block: ranks, lanes, tiles and straight connectors.

Ranks come from the diagram layout (`assign_layers`). A rank is a column when the
flow runs across (`LR`) and a row when it runs down (`TB`); a lane is the other
axis. Every step joins neighbouring ranks of one lane, so a connector is one
straight segment from a tile edge to the next tile edge. Labels sit in the open
gap beside the connector. No I/O, no HTML.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from varde.pages.blocks_render.diagram_layout import Box, assign_layers
from varde.pages.blocks_render.svg import clip_lines

Size = tuple[float, float]
Point = tuple[float, float]

MARGIN = 12.0
BAND_PAD = 10.0
INSET = 4.0
MIN_TILE_W = 96.0
CAPTION_H = 34.0
MIN_LANE_DOWN = 112.0
GAP_ACROSS, GAP_DOWN = 96.0, 72.0
LANE_GAP = 20.0
HEAD_ACROSS, HEAD_DOWN = 26.0, 40.0
LABEL_CHARS, LABEL_LINES, LABEL_CW, LABEL_LH, LABEL_PAD = 12, 3, 6.4, 14.0, 4.0
LABEL_CLIP = 40


@dataclass(frozen=True)
class Screen:
    id: str
    thumb: Size  # drawn size of the wireframe thumbnail
    lane: int


@dataclass(frozen=True)
class Tile:
    id: str
    box: Box  # thumbnail, caption and a thin frame
    thumb_at: Point


@dataclass(frozen=True)
class Link:
    source: str
    target: str
    points: tuple[Point, Point]
    label: Box | None
    lines: tuple[str, ...]


@dataclass(frozen=True)
class Band:
    index: int
    box: Box
    head: float  # height (LR) or width-independent strip (TB) kept for the title


@dataclass(frozen=True)
class Plan:
    width: float
    height: float
    tiles: tuple[Tile, ...]  # in reading order: lane, then rank, then document order
    links: tuple[Link, ...]
    bands: tuple[Band, ...]  # empty when the lanes are not titled


def tile_size(thumb: Size) -> Size:
    return max(thumb[0] + 2 * INSET, MIN_TILE_W), thumb[1] + 2 * INSET + CAPTION_H


def label_lines(label: str) -> tuple[str, ...]:
    return clip_lines(label[:LABEL_CLIP], LABEL_CHARS, LABEL_LINES) if label else ()


def label_size(lines: Sequence[str]) -> Size:
    if not lines:
        return 0.0, 0.0
    return max(len(x) for x in lines) * LABEL_CW + 2 * LABEL_PAD, len(
        lines
    ) * LABEL_LH + LABEL_PAD


def reading_order(screens: Sequence[Screen], ranks: dict[str, int]) -> list[Screen]:
    order = {s.id: n for n, s in enumerate(screens)}
    return sorted(screens, key=lambda s: (s.lane, ranks[s.id], order[s.id]))


def _spans(extents: Sequence[float], gap: float, start: float) -> list[float]:
    starts, at = [], start
    for extent in extents:
        starts.append(at)
        at += extent + gap
    return starts


def _link(a: Box, b: Box, centre: float, label: str, down: bool) -> Link:
    lines = label_lines(label)
    w, h = label_size(lines)
    if down:
        p1, p2 = (centre, a.y + a.h), (centre, b.y)
        mid = (p1[1] + p2[1]) / 2
        box = Box(centre + 6, mid - h / 2, w, h)
    else:
        p1, p2 = (a.x + a.w, centre), (b.x, centre)
        mid = (p1[0] + p2[0]) / 2
        box = Box(mid - w / 2, centre - LABEL_PAD - h, w, h)
    return Link("", "", (p1, p2), box if lines else None, lines)


@dataclass(frozen=True)
class _Grid:
    """Where ranks (main axis) and lanes (cross axis) sit, in drawing units."""

    down: bool
    head: float  # lane title height; 0 when no lane is titled
    rank_ext: list[float]
    main_at: list[float]
    lane_ext: list[float]
    lane_at: list[float]
    centres: list[float]
    main_end: float
    cross_end: float


def _rank_extents(
    screens: Sequence[Screen], ranks: dict[str, int], sizes: dict[str, Size], along: int
) -> list[float]:
    count = max(ranks.values(), default=0) + 1
    return [
        max((sizes[s.id][along] for s in screens if ranks[s.id] == r), default=0.0)
        for r in range(count)
    ]


def _lane_extents(
    screens: Sequence[Screen], sizes: dict[str, Size], across: int, floor: float
) -> list[float]:
    lanes = max([s.lane for s in screens], default=0) + 1
    return [
        max(
            [
                floor,
                *(sizes[s.id][across] + 2 * BAND_PAD for s in screens if s.lane == k),
            ]
        )
        for k in range(lanes)
    ]


def _grid_of(
    screens: Sequence[Screen],
    ranks: dict[str, int],
    sizes: dict[str, Size],
    titled: bool,
    down: bool,
) -> _Grid:
    along, across = (1, 0) if down else (0, 1)  # index into a (w, h) size
    head = (HEAD_DOWN if down else HEAD_ACROSS) if titled else 0.0
    rank_ext = _rank_extents(screens, ranks, sizes, along)
    lane_ext = _lane_extents(screens, sizes, across, MIN_LANE_DOWN if down else 0.0)
    gap = GAP_DOWN if down else GAP_ACROSS
    main0 = MARGIN + BAND_PAD + (head if down else 0.0)
    main_at = _spans(rank_ext, gap, main0)
    main_len = main_at[-1] + rank_ext[-1] - main0
    lane_head = 0.0 if down else head
    lane_at = _spans([e + lane_head for e in lane_ext], LANE_GAP, MARGIN)
    centres = [lane_at[k] + lane_head + lane_ext[k] / 2 for k in range(len(lane_ext))]
    return _Grid(
        down,
        head,
        rank_ext,
        main_at,
        lane_ext,
        lane_at,
        centres,
        main0 + main_len + BAND_PAD,
        lane_at[-1] + lane_head + lane_ext[-1],
    )


def _tile_boxes(
    screens: Sequence[Screen],
    ranks: dict[str, int],
    sizes: dict[str, Size],
    grid: _Grid,
) -> dict[str, Box]:
    along, across = (1, 0) if grid.down else (0, 1)
    boxes: dict[str, Box] = {}
    for s in screens:
        w, h = sizes[s.id]
        rank = ranks[s.id]
        main = grid.main_at[rank] + (grid.rank_ext[rank] - sizes[s.id][along]) / 2
        cross = grid.centres[s.lane] - sizes[s.id][across] / 2
        boxes[s.id] = Box(cross, main, w, h) if grid.down else Box(main, cross, w, h)
    return boxes


def _links_of(
    steps: Sequence[tuple[str, str, str]],
    screens: Sequence[Screen],
    boxes: dict[str, Box],
    grid: _Grid,
) -> list[Link]:
    links = []
    for a, b, label in steps:
        lane = next(s.lane for s in screens if s.id == a)
        made = _link(boxes[a], boxes[b], grid.centres[lane], label, grid.down)
        links.append(Link(a, b, made.points, made.label, made.lines))
    return links


def _bands_of(grid: _Grid, lanes: int) -> tuple[Band, ...]:
    """One band per lane when the lanes are titled: a column down, a row across."""
    if grid.down:
        return tuple(
            Band(
                k,
                Box(grid.lane_at[k], MARGIN, grid.lane_ext[k], grid.main_end - MARGIN),
                grid.head,
            )
            for k in range(lanes)
        )
    return tuple(
        Band(
            k,
            Box(
                MARGIN,
                grid.lane_at[k],
                grid.main_end - MARGIN,
                grid.head + grid.lane_ext[k],
            ),
            grid.head,
        )
        for k in range(lanes)
    )


def plan_flow(
    screens: Sequence[Screen],
    steps: Sequence[tuple[str, str, str]],
    lane_titles: Sequence[str],
    direction: str,
) -> Plan:
    """Tiles, connectors and lane bands; `direction` is `LR` (across) or `TB` (down)."""
    down = direction == "TB"
    ranks = assign_layers([s.id for s in screens], [(a, b) for a, b, _ in steps])
    sizes = {s.id: tile_size(s.thumb) for s in screens}
    titled = any(lane_titles)
    grid = _grid_of(screens, ranks, sizes, titled, down)
    boxes = _tile_boxes(screens, ranks, sizes, grid)
    tiles = tuple(
        Tile(
            s.id,
            boxes[s.id],
            (boxes[s.id].x + (boxes[s.id].w - s.thumb[0]) / 2, boxes[s.id].y + INSET),
        )
        for s in reading_order(screens, ranks)
    )
    bands = _bands_of(grid, len(grid.lane_ext)) if titled else ()
    width, height = (
        (grid.cross_end, grid.main_end) if down else (grid.main_end, grid.cross_end)
    )
    links = _links_of(steps, screens, boxes, grid)
    return Plan(width + MARGIN, height + MARGIN, tiles, tuple(links), bands)
