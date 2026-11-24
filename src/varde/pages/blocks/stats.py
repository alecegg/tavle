"""Block type for a headline strip of numbers: stats."""

from varde.pages.blocks.rules import Fault, is_number
from varde.pages.blocks.spec import BlockSpec, PropertySpec

DIRECTIONS = ("up", "down", "flat")
GOODS = ("up", "down")
TONES = ("neutral", "info", "decision", "risk", "warning", "success")
MIN_ITEMS = 2
MAX_ITEMS = 6
MAX_DECIMALS = 6
SIGNS = ("+", "-", "−")


def delta_direction(item: dict[str, object]) -> str | None:
    """The stated direction, else the sign of the delta; None when neither says."""
    direction = item.get("direction")
    if isinstance(direction, str):
        return direction
    delta = item.get("delta")
    if is_number(delta):
        return "flat" if delta == 0 else "up" if delta > 0 else "down"  # type: ignore[operator]
    if isinstance(delta, str) and delta.strip()[:1] == "+":
        return "up"
    if isinstance(delta, str) and delta.strip()[:1] in SIGNS[1:]:
        return "down"
    return None


def _value_fault(item: dict[str, object], where: str) -> list[Fault]:
    if "value" not in item or is_number(item["value"]):
        return []
    value = item["value"]
    if isinstance(value, str) and value.strip():
        return []
    return [Fault("type", f"{where}: 'value' must be a non-empty string or a number")]


def _decimals_fault(item: dict[str, object], where: str) -> list[Fault]:
    decimals = item.get("decimals")
    if not isinstance(decimals, int) or isinstance(decimals, bool):
        return []  # absent, or a type fault the properties already report
    if 0 <= decimals <= MAX_DECIMALS:
        return []
    return [Fault("type", f"{where}: decimals must be 0 to {MAX_DECIMALS}")]


def _delta_fault(item: dict[str, object], where: str) -> list[Fault]:
    if "delta" not in item:
        return []
    delta = item["delta"]
    if not (is_number(delta) or isinstance(delta, str)):
        return [Fault("type", f"{where}: 'delta' must be a string or number")]
    if not str(delta).strip():
        return [Fault("type", f"{where}: 'delta' must be a non-empty string or number")]
    if delta_direction(item) is None:
        return [Fault("direction", f"{where}: delta needs a direction or a +/- sign")]
    return []


def _item_faults(item: dict[str, object], where: str) -> list[Fault]:
    return (
        _value_fault(item, where)
        + _decimals_fault(item, where)
        + _delta_fault(item, where)
    )


def validate_stats(data: dict[str, object]) -> list[Fault]:
    items = data.get("item")
    if not isinstance(items, list) or not all(isinstance(i, dict) for i in items):
        return []  # absent, or a type fault the properties already report
    faults: list[Fault] = []
    if not MIN_ITEMS <= len(items) <= MAX_ITEMS:
        faults.append(
            Fault("limit", f"stats: {MIN_ITEMS} to {MAX_ITEMS} items; split the block")
        )
    for n, item in enumerate(items, 1):
        faults += _item_faults(item, f"stats: item[{n}]")
    return faults


STATS = BlockSpec(
    "stats",
    "A strip of 2 to 6 headline numbers with an optional change",
    (
        "item: 2 to 6. value is text or a number (numbers get thousands separators;",
        "  decimals sets the places); delta is text or a number, shown as 'up 12%'",
        "  with an arrow; direction is up, down or flat (else the sign of delta);",
        "  good says which direction is good (up or down), so a good move reads",
        "  green and a bad one red; flat is neutral; tone overrides the colour.",
        "The word up, down or flat is always in the text, never colour alone.",
    ),
    r"""stats = stats(
  item: [
    {"label": "Requests", "value": 1204331, "delta": "12%", "good": "up",
     "direction": "up"},
    {"label": "p95 latency", "value": "212 ms", "delta": "-8%", "good": "down"},
    {"label": "Error rate", "value": 0.4, "decimals": 2, "delta": "0.1 pt",
     "direction": "up", "good": "down"},
  ],
)
""",
    validate_stats,
    properties=(
        PropertySpec(
            "item",
            "list",
            required=True,
            items="object",
            fields=(
                PropertySpec("label", "string", required=True, nonempty=True),
                # value and delta take text or a number; the validator checks them.
                PropertySpec("value", "any", required=True),
                PropertySpec("delta", "any"),
                PropertySpec("direction", "string", enum=DIRECTIONS),
                PropertySpec("good", "string", enum=GOODS),
                PropertySpec("tone", "string", enum=TONES),
                PropertySpec("note", "string", nonempty=True),
                PropertySpec("decimals", "integer"),
            ),
        ),
    ),
)
