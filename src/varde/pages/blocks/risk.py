"""Block type for a risk matrix: likelihood by impact with a mitigation list."""

from varde.pages.blocks.rules import Fault, duplicates, tables
from varde.pages.blocks.spec import BlockSpec, PropertySpec

LEVELS = ("low", "medium", "high")
MAX_ITEMS = 200


def _unique_id_faults(items: list[dict[str, object]]) -> list[Fault]:
    ids = [i for r in items if isinstance(i := r.get("id"), str)]
    return [Fault("duplicate-id", f"risk: duplicate id '{d}'") for d in duplicates(ids)]


def validate_risk(data: dict[str, object]) -> list[Fault]:
    items = data.get("item")
    if not isinstance(items, list):
        return []
    faults = (
        [Fault("limit", f"risk: at most {MAX_ITEMS} items; split it")]
        if len(items) > MAX_ITEMS
        else []
    )
    return faults + _unique_id_faults(tables(data, "item", "risk"))


RISK = BlockSpec(
    "risks",
    "Risks placed by likelihood and impact, with severity and mitigations",
    (
        "title: caption.",
        "item: likelihood and impact are low, medium or high; ids are unique; at",
        "  most 200 items.",
        "Severity is likelihood x impact (low=1, medium=2, high=3): 1-2 low,",
        "3-4 medium, 6 high, 9 critical. It is shown as a glyph and a word.",
        "The 3x3 grid is a summary; the full list below it carries every",
        "risk. A grid cell shows at most 4 ids and then '+N'.",
    ),
    r"""risks = risks(
  title: "Launch risks",
  item: [
    {"id": "R1", "label": "Vendor patch slips", "likelihood": "high", "impact": "high",
     "mitigation": "Ship behind a flag.", "owner": "Platform"},
    {"id": "R2", "label": "Docs lag", "likelihood": "medium", "impact": "low"},
  ],
)
""",
    validate_risk,
    properties=(
        PropertySpec("title", "string", nonempty=True),
        PropertySpec(
            "item",
            "list",
            required=True,
            nonempty=True,
            items="object",
            fields=(
                PropertySpec("id", "string", required=True, nonempty=True),
                PropertySpec("label", "string", required=True, nonempty=True),
                PropertySpec("likelihood", "string", required=True, enum=LEVELS),
                PropertySpec("impact", "string", required=True, enum=LEVELS),
                PropertySpec("mitigation", "string", nonempty=True),
                PropertySpec("owner", "string", nonempty=True),
            ),
        ),
    ),
)
