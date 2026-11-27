"""Block type for a state machine: states and labelled transitions."""

from ..blocks.rules import Fault, duplicates, tables
from ..blocks.spec import BlockSpec, PropertySpec

KINDS = ("initial", "normal", "final", "error")
MAX_STATES = 40


def _initial_faults(entries: list[dict[str, object]]) -> list[Fault]:
    faults: list[Fault] = []
    initial = sum(1 for s in entries if s.get("kind") == "initial")
    if entries and initial == 0:
        faults.append(Fault("no-initial", "state: one state must have kind initial"))
    if initial > 1:
        faults.append(Fault("two-initial", "state: only one state may be initial"))
    return faults


def _state_faults(data: dict[str, object]) -> tuple[list[Fault], list[str]]:
    faults: list[Fault] = []
    entries = tables(data, "states")
    names = [n for s in entries if isinstance(n := s.get("id"), str)]
    faults += [
        Fault("state-duplicate", f"state: state id '{name}' is used more than once")
        for name in duplicates(names)
    ]
    if len(entries) > MAX_STATES:
        faults.append(Fault("too-many", f"state: at most {MAX_STATES} states"))
    return faults + _initial_faults(entries), names


def _end_fault(move: dict[str, object], key: str, names: list[str], where: str):
    end = move.get(key)
    if isinstance(end, str) and end not in names:
        return [Fault("transition-state", f"{where}: {key} '{end}' is not a state id")]
    return []


def _move_faults(data: dict[str, object], names: list[str]) -> list[Fault]:
    faults: list[Fault] = []
    for n, move in enumerate(tables(data, "transitions"), 1):
        where = f"transitions[{n}]"
        faults += _end_fault(move, "from", names, where)
        faults += _end_fault(move, "to", names, where)
    return faults


def validate_state(data: dict[str, object]) -> list[Fault]:
    state_faults, names = _state_faults(data)
    return state_faults + _move_faults(data, names)


STATE = BlockSpec(
    "state",
    "A state machine: states and labelled transitions, drawn as SVG",
    (
        "states: 1 to 40; id is the unique state name; label is the text in its",
        "  box; kind defaults to normal; initial (exactly one) gets a start dot,",
        "  final has a double border and error a cross mark; note is shown in the",
        "  text list.",
        "transitions: from and to are state ids; the same id draws a self-loop;",
        "  label is an event or action; guard is shown as [guard].",
        "desc: what the machine models, for screen readers.",
        "A state no path from the initial state reaches is marked unreachable.",
        "Transitions are always also listed as text: 'A to B on label [guard]'.",
    ),
    r"""state = state(
  title: "Job",
  desc: "A job waits, runs, and ends done or failed; failed jobs retry.",
  states: [
    {"id": "idle", "label": "Idle", "kind": "initial"},
    {"id": "run", "label": "Running"},
    {"id": "done", "label": "Done", "kind": "final"},
    {"id": "bad", "label": "Failed", "kind": "error"},
  ],
  transitions: [
    {"from": "idle", "to": "run", "label": "start"},
    {"from": "run", "to": "done", "label": "finish"},
    {"from": "run", "to": "bad", "label": "crash"},
    {"from": "bad", "to": "run", "label": "retry", "guard": "attempts < 3"},
    {"from": "run", "to": "run", "label": "heartbeat"},
  ],
)
""",
    validate_state,
    properties=(
        PropertySpec(
            "states",
            "list",
            required=True,
            nonempty=True,
            items="object",
            fields=(
                PropertySpec("id", "string", required=True, nonempty=True),
                PropertySpec("label", "string", required=True, nonempty=True),
                PropertySpec("kind", "string", enum=KINDS),
                PropertySpec("note", "string", nonempty=True),
            ),
        ),
        PropertySpec(
            "transitions",
            "list",
            nonempty=True,
            items="object",
            fields=(
                PropertySpec("from", "string", required=True),
                PropertySpec("to", "string", required=True),
                PropertySpec("label", "string", nonempty=True),
                PropertySpec("guard", "string", nonempty=True),
            ),
        ),
        PropertySpec("desc", "string", required=True, nonempty=True),
        PropertySpec("title", "string", nonempty=True),
    ),
)
