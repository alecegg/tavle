"""Block type for process: flow."""

from varde.pages.blocks.diagrams import empty_list_faults
from varde.pages.blocks.rules import Fault, duplicates, tables
from varde.pages.blocks.spec import BlockSpec, PropertySpec


def validate_flow(data: dict[str, object]) -> list[Fault]:
    faults = empty_list_faults(data, ("step",), "flow")
    steps = tables(data, "step", "flow")
    ids = [n for s in steps if isinstance(n := s.get("id"), str)]
    faults += [
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
        "title        optional text",
        "step: list of {id, text, next}, one per step",
        "  id    unique step name",
        "  text  what happens",
        "  next  optional list of step ids; several entries are branches",
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
        PropertySpec("title", "string"),
        PropertySpec(
            "step",
            "list",
            required=True,
            items="object",
            fields=(
                PropertySpec("id", "string", required=True),
                PropertySpec("text", "string", required=True),
                PropertySpec("next", "list", items="string"),
            ),
        ),
    ),
)
