"""Component `deps`: a task dependency graph; props are the edges."""

from varde.pages.blocks.rules import Fault
from varde.pages.blocks.spec import BlockSpec, PropertySpec

_FORBIDDEN = (":", ",", "\n", "#")


def _name_fault(name: object, where: str) -> list[Fault]:
    if (
        isinstance(name, str)
        and name.strip()
        and not any(c in name for c in _FORBIDDEN)
    ):
        return []
    return [Fault("type", f"{where}: names must be text without ':', ',' or '#'")]


def validate_deps(data: dict[str, object]) -> list[Fault]:
    edges = data.get("edges")
    if not isinstance(edges, dict):
        return []  # absent or not a table: the properties report it
    faults: list[Fault] = []
    for task, needs in edges.items():
        faults += _name_fault(task, "deps.edges")
        if not isinstance(needs, list):
            faults.append(Fault("type", f"deps.edges.{task} must be a list of tasks"))
            continue
        for need in needs:
            faults += _name_fault(need, f"deps.edges.{task}")
    return faults + _status_faults(edges, data.get("status"))


def _named_tasks(edges: dict[object, object]) -> set[object]:
    needed = {
        n
        for needs in edges.values()
        if isinstance(needs, list)
        for n in needs
        if isinstance(n, str)
    }
    return set(edges) | needed


def _status_faults(edges: dict[object, object], status: object) -> list[Fault]:
    """A status names a task in the graph and is a word."""
    if not isinstance(status, dict):
        return []  # absent or not a table: the properties report it
    tasks = _named_tasks(edges)
    faults = [
        Fault("value", f"deps.status.{name}: task is not in edges")
        for name in status
        if name not in tasks
    ]
    faults += [
        Fault("type", f"deps.status.{name} must be text")
        for name, word in status.items()
        if not isinstance(word, str)
    ]
    return faults


DEPS = BlockSpec(
    "deps",
    "A task dependency graph drawn from edges",
    (
        "edges: a table mapping each task id to the list of tasks it depends on.",
        "status: an optional table mapping task ids to status words.",
    ),
    r"""deps = deps(
  edges: {"a": [], "b": ["a"], "c": ["a", "b"]},
  status: {"a": "done", "b": "in progress"},
)
""",
    validate_deps,
    block_type="status",
    properties=(
        PropertySpec("edges", "object", required=True),
        PropertySpec("status", "object"),
    ),
)
