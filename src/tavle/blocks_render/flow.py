"""Props for the flow block: a top-down diagram of step cards laid out on the server.

A flow is a graph preset: each step is a node labelled with its text and each
`next` entry is an edge, laid out by the diagram layered layout. The ordered list
of steps stays in the page as the text alternative; `static/components/flow.js`
builds the DOM; `static/flow.js` adds the dependency highlight and pan and zoom.
"""

from varde.ui.blocks_render.common import as_dict, as_list
from varde.ui.blocks_render.diagram_layout import (
    MIN_H,
    EdgeSpec,
    NodeSpec,
    layout_graph,
)
from varde.ui.blocks_render.diagrams import state_view


def _steps(data: dict[str, object]) -> list[dict[str, object]]:
    """Steps in document order; a repeated id keeps its first step."""
    seen: dict[str, dict[str, object]] = {}
    for step in map(as_dict, as_list(data.get("step"))):
        seen.setdefault(str(step["id"]), step)
    return list(seen.values())


def _targets(step: dict[str, object], known: set[str]) -> list[str]:
    return [str(t) for t in as_list(step.get("next")) if str(t) in known]


def _specs(
    steps: list[dict[str, object]],
) -> tuple[list[NodeSpec], list[EdgeSpec]]:
    known = {str(s["id"]) for s in steps}
    nodes = [
        NodeSpec(
            str(s["id"]),
            str(s["text"]),
            "box" if _targets(s, known) else "rounded",
        )
        for s in steps
    ]
    edges = [
        EdgeSpec(str(s["id"]), target)
        for s in steps
        for target in dict.fromkeys(_targets(s, known))
    ]
    return nodes, edges


def _summary(data: dict[str, object]) -> str:
    count = len(_steps(data))
    return f"flow of {count} step{'' if count == 1 else 's'}"


def copy_text(data: dict[str, object]) -> str:
    """Plain text for the Copy entry: the steps in order, each with what follows."""
    steps = _steps(data)
    known = {str(s["id"]) for s in steps}
    lines = [f"{data.get('title', 'Flow')} ({_summary(data)})"]
    for n, step in enumerate(steps, 1):
        line = f"{n}. {step['id']}: {step['text']}"
        targets = _targets(step, known)
        if targets:
            line += f" -> {', '.join(targets)}"
        lines.append(line)
    return "\n".join(lines)


def _alternative(data: dict[str, object]) -> dict[str, object]:
    steps = _steps(data)
    known = {str(s["id"]) for s in steps}
    return {
        "summary": _summary(data),
        "steps": [
            {"id": str(s["id"]), "text": str(s["text"]), "next": _targets(s, known)}
            for s in steps
        ],
    }


def flow_props(data: dict[str, object]) -> dict[str, object]:
    """Heading, one layout of the steps (as shapes) and the steps as text."""
    shown: dict[str, object] = {
        "heading": str(data["title"]) if "title" in data else "",
        "alt": _alternative(data),
    }
    if not _steps(data):
        return shown
    nodes, edges = _specs(_steps(data))
    drawn = state_view(0, layout_graph(nodes, edges, "TB"), [], {})
    return {
        **shown,
        "title": str(data.get("title", "Flow")),
        "desc": f"{_summary(data)}, top to bottom",
        "unit": f"{MIN_H:g}",
        "view": drawn,
        "copy": copy_text(data),
    }
