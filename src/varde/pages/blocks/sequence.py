"""Block type for a sequence diagram: actors, ordered steps, optional groups."""

from varde.pages.blocks.diagrams import empty_list_faults
from varde.pages.blocks.rules import Fault, duplicates, tables
from varde.pages.blocks.spec import BlockSpec, PropertySpec

KINDS = ("call", "return", "async", "note")
MAX_ACTORS = 12
MAX_STEPS = 200


def _actor_faults(data: dict[str, object]) -> tuple[list[Fault], list[str]]:
    faults: list[Fault] = []
    entries = tables(data, "actors", "sequence")
    names = [n for a in entries if isinstance(n := a.get("id"), str)]
    faults += [
        Fault("actor-duplicate", f"sequence: actor id '{name}' is used more than once")
        for name in duplicates(names)
    ]
    if len(entries) > MAX_ACTORS:
        faults.append(Fault("too-many", f"sequence: at most {MAX_ACTORS} actors"))
    return faults, names


def _end_fault(step: dict[str, object], key: str, actors: list[str], where: str):
    end = step.get(key)
    if isinstance(end, str) and end not in actors:
        return [Fault("step-actor", f"{where}: {key} '{end}' is not an actor id")]
    return []


def _step_faults(step: dict[str, object], actors: list[str], where: str) -> list[Fault]:
    return _end_fault(step, "from", actors, where) + _end_fault(
        step, "to", actors, where
    )


def _steps_faults(data: dict[str, object], actors: list[str]) -> list[Fault]:
    faults: list[Fault] = []
    entries = tables(data, "steps", "sequence")
    if len(entries) > MAX_STEPS:
        faults.append(Fault("too-many", f"sequence: at most {MAX_STEPS} steps"))
    for n, step in enumerate(entries, 1):
        faults += _step_faults(step, actors, f"steps[{n}]")
    return faults


def validate_sequence(data: dict[str, object]) -> list[Fault]:
    faults = empty_list_faults(data, ("actors", "steps"), "sequence")
    actor_faults, actors = _actor_faults(data)
    return faults + actor_faults + _steps_faults(data, actors)


SEQUENCE = BlockSpec(
    "sequence",
    "A sequence diagram of actors and ordered steps, drawn as SVG",
    (
        "actors: list of {id, label}, 1 to 12",
        "  id     unique actor name; label is the text over its lifeline",
        "steps: list of {from, to, text, kind, group}, 1 to 200, in order",
        "  from, to  actor ids; the same id draws a self-call loop",
        "  text      the message",
        "  kind      optional: call (default, solid), return (dashed),",
        "            async (open head) or note (a box across from..to)",
        "  group     optional label; neighbouring steps with the same label sit",
        "            in one labelled frame (alt, loop, opt style)",
        "desc        what the diagram shows, for screen readers",
        "title       optional text",
        "  The steps are always also listed as text: 'A to B: text'.",
    ),
    r"""sequence = sequence(
  title: "Sign in",
  desc: "The browser signs a user in through the API and the user store.",
  actors: [
    {"id": "b", "label": "Browser"},
    {"id": "api", "label": "API"},
    {"id": "db", "label": "Users"},
  ],
  steps: [
    {"from": "b", "to": "api", "text": "POST /login"},
    {"from": "api", "to": "db", "text": "find user", "group": "cache miss"},
    {"from": "db", "to": "api", "text": "row", "kind": "return", "group": "cache miss"},
    {"from": "api", "to": "api", "text": "check password"},
    {"from": "api", "to": "b", "text": "session cookie", "kind": "return"},
  ],
)
""",
    validate_sequence,
    properties=(
        PropertySpec(
            "actors",
            "list",
            required=True,
            items="object",
            fields=(
                PropertySpec("id", "string", required=True),
                PropertySpec("label", "string", required=True),
            ),
        ),
        PropertySpec(
            "steps",
            "list",
            required=True,
            items="object",
            fields=(
                PropertySpec("from", "string", required=True),
                PropertySpec("to", "string", required=True),
                PropertySpec("text", "string", required=True),
                PropertySpec("kind", "string", enum=KINDS),
                PropertySpec("group", "string"),
            ),
        ),
        PropertySpec("desc", "string", required=True),
        PropertySpec("title", "string"),
    ),
)
