"""Block type for phases and milestones: timeline."""

from varde.pages.blocks.rules import Fault
from varde.pages.blocks.spec import BlockSpec, PropertySpec

ORIENTATIONS = ("vertical", "horizontal")
STATUSES = ("done", "active", "planned", "blocked")
MAX_VERTICAL = 200
MAX_HORIZONTAL = 24


def _limit_fault(count: int, horizontal: bool) -> list[Fault]:
    cap = MAX_HORIZONTAL if horizontal else MAX_VERTICAL
    if count <= cap:
        return []
    layout = "horizontal" if horizontal else "vertical"
    return [Fault("limit", f"timeline: at most {cap} items when {layout}; split it")]


def validate_timeline(data: dict[str, object]) -> list[Fault]:
    items = data.get("item")
    if not isinstance(items, list):
        return []
    return _limit_fault(len(items), data.get("orientation") == "horizontal")


TIMELINE = BlockSpec(
    "timeline",
    "Phases and milestones in order, each with a status",
    (
        "title: caption.",
        "orientation: vertical (default) or horizontal; horizontal is a row on wide",
        "  pages (at most 24 items, scrolls if it does not fit) and a vertical list",
        "  on narrow ones.",
        "item: at most 200 items (24 horizontal); when is free text (a date or a",
        "  phase name); status is done, active, planned or blocked.",
        "Status is a glyph plus a word, never colour alone; the first active",
        "item is marked as the current step.",
    ),
    r"""timeline = timeline(
  title: "Rollout",
  item: [
    {"when": "Week 1", "label": "Design review", "status": "done"},
    {"when": "Week 2", "label": "Build", "status": "active", "owner": "Platform"},
    {"when": "Week 4", "label": "Launch", "status": "planned",
     "note": "Needs sign-off."},
  ],
)
""",
    validate_timeline,
    properties=(
        PropertySpec("title", "string", nonempty=True),
        PropertySpec("orientation", "string", enum=ORIENTATIONS),
        PropertySpec(
            "item",
            "list",
            required=True,
            nonempty=True,
            items="object",
            fields=(
                PropertySpec("when", "string", required=True, nonempty=True),
                PropertySpec("label", "string", required=True, nonempty=True),
                PropertySpec("status", "string", required=True, enum=STATUSES),
                PropertySpec("note", "string", nonempty=True),
                PropertySpec("owner", "string", nonempty=True),
            ),
        ),
    ),
)
