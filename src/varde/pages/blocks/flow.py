"""Block type for process: flow."""

from varde.pages.blocks.rules import Fault, duplicates, tables
from varde.pages.blocks.spec import BlockSpec, PropertySpec


def validate_flow(data: dict[str, object]) -> list[Fault]:
    steps = tables(data, "step", "flow")
    ids = [n for s in steps if isinstance(n := s.get("id"), str)]
    faults = [
        Fault("step-duplicate", f"flow: step id '{name}' is used more than once")
        for name in duplicates(ids)
    ]
    for n, step in enumerate(steps, 1):
        where = f"step[{n}]"
        targets = step.get("next")
        if not isinstance(targets, list):
            continue
        faults += [
            Fault("step-target", f"{where}: next '{t}' is not a step id")
            for t in targets
            if isinstance(t, str) and t not in ids
        ]
    return faults


FLOW = BlockSpec(
    "flow",
    "Steps and the steps that can follow each",
    (
        "title: text.",
        "step: one per step; id is a unique step name; text is what happens; next",
        "  lists step ids, and several entries are branches.",
    ),
    r"""flow = flow(
  title: "Checkout",
  step: [
    {"id": "cart", "text": "Review cart", "next": ["pay"]},
    {"id": "pay", "text": "Pay", "next": ["done", "failed"]},
    {"id": "done", "text": "Show receipt"},
    {"id": "failed", "text": "Show error", "next": ["pay"]},
  ],
)
""",
    validate_flow,
    properties=(
        PropertySpec("title", "string", nonempty=True),
        PropertySpec(
            "step",
            "list",
            required=True,
            nonempty=True,
            items="object",
            fields=(
                PropertySpec("id", "string", required=True, nonempty=True),
                PropertySpec("text", "string", required=True, nonempty=True),
                PropertySpec("next", "list", nonempty=True, items="string"),
            ),
        ),
    ),
)
