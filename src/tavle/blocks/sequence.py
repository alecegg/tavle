"""Block type for a sequence diagram: actors, ordered steps, optional groups."""

from ..blocks.rules import Fault, duplicates, tables
from ..blocks.spec import BlockSpec, PropertySpec

KINDS = ("call", "return", "async", "note")
MAX_ACTORS = 12
MAX_STEPS = 200


def _actor_faults(data: dict[str, object]) -> tuple[list[Fault], list[str]]:
    faults: list[Fault] = []
    entries = tables(data, "actors")
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
    if not actors:
        return []  # no actor to refer to; the properties report the empty list
    return _end_fault(step, "from", actors, where) + _end_fault(
        step, "to", actors, where
    )


def _steps_faults(data: dict[str, object], actors: list[str]) -> list[Fault]:
    faults: list[Fault] = []
    entries = tables(data, "steps")
    if len(entries) > MAX_STEPS:
        faults.append(Fault("too-many", f"sequence: at most {MAX_STEPS} steps"))
    for n, step in enumerate(entries, 1):
        faults += _step_faults(step, actors, f"steps[{n}]")
    return faults


def validate_sequence(data: dict[str, object]) -> list[Fault]:
    actor_faults, actors = _actor_faults(data)
    return actor_faults + _steps_faults(data, actors)


SEQUENCE = BlockSpec(
    "sequence",
    "A sequence diagram of actors and ordered steps, drawn as SVG",
    (
        "actors: 1 to 12; id is the unique actor name; label is the text over its",
        "  lifeline.",
        "steps: 1 to 200, in order. from and to are actor ids; the same id draws a",
        "  self-call loop; text is the message; kind defaults to call (solid), the",
        "  others are return (dashed), async (open head) and note (a box across",
        "  from..to); neighbouring steps with the same group label sit in one",
        "  labelled frame (alt, loop, opt style).",
        "desc: what the diagram shows, for screen readers.",
        "The steps are always also listed as text: 'A to B: text'.",
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
            nonempty=True,
            items="object",
            fields=(
                PropertySpec("id", "string", required=True, nonempty=True),
                PropertySpec("label", "string", required=True, nonempty=True),
            ),
        ),
        PropertySpec(
            "steps",
            "list",
            required=True,
            nonempty=True,
            items="object",
            fields=(
                PropertySpec("from", "string", required=True),
                PropertySpec("to", "string", required=True),
                PropertySpec("text", "string", required=True, nonempty=True),
                PropertySpec("kind", "string", enum=KINDS),
                PropertySpec("group", "string", nonempty=True),
            ),
        ),
        PropertySpec("desc", "string", required=True, nonempty=True),
        PropertySpec("title", "string", nonempty=True),
    ),
)
