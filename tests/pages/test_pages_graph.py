import re

from varde.pages.template import static_css


def edges(text: str) -> dict[str, list[str]]:
    """`task: dep, dep` lines as the `edges` prop."""
    result: dict[str, list[str]] = {}
    for line in text.splitlines():
        task, sep, rest = line.partition(":")
        if sep and task.strip() and not task.startswith("#"):
            deps = [d.strip() for d in rest.split(",") if d.strip()]
            result.setdefault(task.strip(), []).extend(deps)
    return result


FORBIDDEN = re.compile(r"<script|foreignObject|<[^>]*\s(style|on\w+)=", re.IGNORECASE)


def test_graph_css_makes_labels_readable_and_edges_unfilled():
    css = static_css()
    assert ".dep-graph .node text { fill: var(--vd-text)" in css
    assert ".dep-graph .edge { fill: none" in css
    assert ".dep-graph .arrow { fill: var(--vd-text-secondary)" in css
