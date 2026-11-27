"""Block type for numbers: chart."""

import math

from ..blocks.chart_notes import NOTE_PROPERTIES, note_rule_faults
from ..blocks.rules import Fault, is_number, tables
from ..blocks.spec import BlockSpec, PropertySpec

_CHART_KINDS = ("bar", "line", "area", "scatter", "donut", "sparkline", "combo")
MAX_SERIES = 12
MAX_POINTS = 500
MAX_DECIMALS = 6


def _bool_faults(data: dict[str, object]) -> list[Fault]:
    faults: list[Fault] = []
    if data.get("stack") is True and data.get("kind") not in ("bar", "combo"):
        faults.append(Fault("type", "chart.stack applies to bar or combo charts"))
    if data.get("horizontal") is True and data.get("kind") != "bar":
        faults.append(Fault("type", "chart.horizontal applies to bar charts"))
    return faults


def _decimals_faults(data: dict[str, object]) -> list[Fault]:
    decimals = data.get("decimals")
    if not isinstance(decimals, int) or isinstance(decimals, bool):
        return []  # absent, or a type fault the properties already report
    if 0 <= decimals <= MAX_DECIMALS:
        return []
    return [Fault("type", "chart.decimals must be a whole number from 0 to 6")]


def _labels_faults(data: dict[str, object]) -> list[Fault]:
    if "labels" in data or data.get("kind") == "scatter":
        return []
    return [Fault("missing-key", "chart: missing required key 'labels'")]


def _numbers(value: object) -> list[float] | None:
    """The list when it holds only numbers; None when absent or a type fault."""
    if isinstance(value, list) and all(is_number(v) for v in value):
        return value
    return None


def _values_faults(
    kind: object, labels: object, series: dict[str, object], where: str
) -> list[Fault]:
    values = _numbers(series.get("values"))
    if not values:
        return []  # absent, empty or a type fault the properties already report
    if not all(math.isfinite(v) for v in values):
        return [Fault("type", f"{where}.values must be a list of finite numbers")]
    if len(values) > MAX_POINTS:
        return [Fault("too-many", f"{where}.values: at most {MAX_POINTS} numbers")]
    if kind == "donut" and any(v < 0 for v in values):
        return [Fault("donut-negative", f"{where}.values must not be negative")]
    if kind != "scatter" and isinstance(labels, list) and len(values) != len(labels):
        message = (
            f"{where}.values has {len(values)} numbers, "
            f"expected {len(labels)} (one per label)"
        )
        return [Fault("series-length", message)]
    return []


def _scatter_faults(series: dict[str, object], where: str) -> list[Fault]:
    if "x" not in series:
        return [Fault("type", f"{where}.x must be a list of numbers, one per value")]
    xs, values = _numbers(series["x"]), series.get("values")
    if xs is None:
        return []  # a type fault the properties already report
    if not all(math.isfinite(x) for x in xs):
        return [Fault("type", f"{where}.x must be a list of numbers, one per value")]
    if isinstance(values, list) and len(xs) != len(values):
        message = f"{where}.x has {len(xs)} numbers, expected {len(values)}"
        return [Fault("series-length", message)]
    return []


def _combo_faults(kind: object, series: dict[str, object], where: str) -> list[Fault]:
    if kind == "combo":
        return []
    return [
        Fault("type", f"{where}.{key} applies to combo charts")
        for key in ("axis", "type")
        if key in series
    ]


def _one_series_faults(
    kind: object, labels: object, series: dict[str, object], where: str
) -> list[Fault]:
    faults = _values_faults(kind, labels, series, where)
    if kind == "scatter":
        faults += _scatter_faults(series, where)
    elif "x" in series:
        faults.append(Fault("type", f"{where}.x applies to scatter charts"))
    return faults + _combo_faults(kind, series, where)


def _series_faults(data: dict[str, object]) -> list[Fault]:
    kind = data.get("kind")
    labels = data.get("labels") or None  # an empty list is reported by the properties
    items = tables(data, "series")
    faults: list[Fault] = []
    if len(items) > MAX_SERIES:
        faults.append(Fault("too-many", f"chart.series: at most {MAX_SERIES} series"))
    if kind in ("donut", "sparkline") and len(items) > 1:
        faults.append(Fault("type", f"chart: a {kind} takes one series"))
    for n, series in enumerate(items, 1):
        faults += _one_series_faults(kind, labels, series, f"series[{n}]")
    return faults


def validate_chart(data: dict[str, object]) -> list[Fault]:
    faults = _decimals_faults(data) + _bool_faults(data) + note_rule_faults(data)
    return faults + _labels_faults(data) + _series_faults(data)


CHART = BlockSpec(
    "chart",
    "A bar, line, area, scatter, donut, sparkline or combo chart from numbers",
    (
        "labels: the x labels (donut: slice names; scatter: omit).",
        "desc: a one-sentence summary. right_unit: unit of the right axis (combo).",
        "decimals: digits after the point, 0 to 6.",
        "stack and horizontal apply to bar; stack also to combo.",
        "notes: up to 12 markers and bands. A marker has x (a label; scatter: a",
        "  number) and a label; tone defaults to info. A band has from and to",
        "  instead of x; its from is not after its to (scatter: from below to,",
        "  inside the data).",
        "series: one per series, up to 12; values has one number per label; x is",
        "  for scatter only, one number per value; axis (left or right) and type",
        "  (bar or line) are for combo only.",
    ),
    r"""chart = chart(
  kind: "bar",
  title: "Latency",
  unit: "ms",
  desc: "p95 latency fell by about half after the cache change.",
  labels: ["before", "after"],
  series: [
    {"name": "p50", "values": [120, 80]},
    {"name": "p95", "values": [400, 210]},
  ],
  notes: [
    {"x": "after", "label": "cache"},
    {"from": "before", "to": "after", "label": "rollout", "tone": "warning"},
  ],
)
""",
    validate_chart,
    properties=(
        PropertySpec("kind", "string", required=True, enum=_CHART_KINDS),
        PropertySpec("labels", "list", items="string", nonempty=True),
        PropertySpec("title", "string", nonempty=True),
        PropertySpec("unit", "string", nonempty=True),
        PropertySpec("desc", "string", nonempty=True),
        PropertySpec("right_unit", "string", nonempty=True),
        PropertySpec("decimals", "integer"),
        PropertySpec("stack", "boolean"),
        PropertySpec("horizontal", "boolean"),
        PropertySpec(
            "notes",
            "list",
            nonempty=True,
            items="object",
            fields=NOTE_PROPERTIES,
        ),
        PropertySpec(
            "series",
            "list",
            required=True,
            nonempty=True,
            items="object",
            fields=(
                PropertySpec("name", "string", required=True, nonempty=True),
                PropertySpec(
                    "values", "list", required=True, nonempty=True, items="number"
                ),
                PropertySpec("x", "list", items="number"),
                PropertySpec("axis", "string", enum=("left", "right")),
                PropertySpec("type", "string", enum=("bar", "line")),
            ),
        ),
    ),
)
