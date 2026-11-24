"""Block type for a static checklist with progress: checklist."""

from varde.pages.blocks.rules import Fault, tables
from varde.pages.blocks.spec import BlockSpec, PropertySpec

STATUSES = ("done", "open", "blocked")
MAX_ITEMS = 500


def _agree_faults(item: dict[str, object], where: str) -> list[Fault]:
    status = item.get("status")
    checked = item.get("checked")
    if status not in STATUSES or not isinstance(checked, bool):
        return []
    if checked == (status == "done"):
        return []
    return [Fault("conflict", f"{where}: checked and status disagree")]


def validate_checklist(data: dict[str, object]) -> list[Fault]:
    items = data.get("items")
    if not isinstance(items, list):
        return []
    faults = (
        [Fault("limit", f"checklist: at most {MAX_ITEMS} items")]
        if len(items) > MAX_ITEMS
        else []
    )
    for n, item in enumerate(tables(data, "items", "checklist"), 1):
        faults += _agree_faults(item, f"checklist: items[{n}]")
    return faults


CHECKLIST = BlockSpec(
    "checklist",
    "A static checklist with a state word per item and a progress count",
    (
        "title: heading.",
        "items: up to 500. label is plain text with `code` spans; note shows muted",
        "  under the label; status defaults to open; checked: true means done and",
        "  must agree with status.",
        "Shows the count as 'N of M done' beside a progress bar. Not interactive.",
    ),
    r"""checklist = checklist(
  title: "Acceptance",
  items: [
    {"label": "Queue keeps order", "status": "done"},
    {"label": "Retry uses `backoff`", "note": "API spec", "status": "blocked"},
    {"label": "Docs updated"},
  ],
)
""",
    validate_checklist,
    properties=(
        PropertySpec("title", "string", nonempty=True),
        PropertySpec(
            "items",
            "list",
            required=True,
            items="object",
            fields=(
                PropertySpec("label", "string", required=True, nonempty=True),
                PropertySpec("id", "string", nonempty=True),
                PropertySpec("checked", "boolean"),
                PropertySpec("note", "string", nonempty=True),
                PropertySpec("status", "string", enum=STATUSES),
            ),
        ),
    ),
)
