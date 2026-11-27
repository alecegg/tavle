"""Page fence scanning, component examples and the validators' fault reports."""

import pytest
from ui_fence import example_fence

from tavle import blocks
from tavle.lines import parse_lines
from tavle.page.fences import Fence, _id_text, find_fences
from tavle.page.markdown_syntax import FENCE
from tavle.page.page_check import check
from tavle.page.render import render_page


def reference_find_fences(text, langs):
    """The scanner as it was before `scan_fences` (pinned for the differential test)."""
    lines = text.expandtabs(4).splitlines()
    found, i = [], 0
    while i < len(lines):
        opening = FENCE.match(lines[i])
        if opening is None:
            i += 1
            continue
        indent, marker, lang = len(opening.group(1)), opening.group(2), opening.group(3)
        body, j = [], i + 1
        while j < len(lines) and not (
            (closing := FENCE.match(lines[j]))
            and closing.group(2)[0] == marker[0]
            and len(closing.group(2)) >= len(marker)
            and not closing.group(3)
            and not closing.group(4).strip()
        ):
            body.append(lines[j][min(indent, len(lines[j]) - len(lines[j].lstrip())) :])
            j += 1
        if lang in langs:
            found.append(
                Fence(lang, i + 1, _id_text(opening.group(4)), "\n".join(body))
            )
        i = j + 1
    return found


def test_find_fences_matches_the_reference_scanner():
    import random

    rng = random.Random(7)  # noqa: S311 - test data
    pieces = [
        "```",
        "~~~",
        "````",
        "decision",
        "ui",
        "id=a",
        "  ",
        "\t",
        "x = 1",
        "",
        "text",
        " id=b",
    ]
    for _ in range(3000):
        lines = [
            "".join(rng.choices(pieces, k=rng.randint(0, 4)))
            for _ in range(rng.randint(0, 9))
        ]
        text = rng.choice(["\n", "\r\n"]).join(lines)
        langs = frozenset({"decision", "ui", ""})
        assert find_fences(text, langs) == reference_find_fences(text, langs)


@pytest.mark.parametrize("name", sorted(blocks.COMPONENT_SPECS))
def test_every_component_example_is_one_valid_statement_that_renders(name):
    spec = blocks.COMPONENT_SPECS[name]
    (statement,) = parse_lines(spec.example).statements
    assert statement.id == name and statement.component == name
    doc = example_fence(spec.example)
    # a container's example names ids that other statements of a real page hold
    assert [e for e in check(doc) if not e.rule.startswith("container-")] == []
    assert "vb-error" not in render_page(doc, "t.md").body


CHANGE_WORDS = "added, modified, removed, renamed"
BAD_NAME = "names must be text without ':', ',' or '#'"


def ids(prefix: str, count: int) -> list[dict[str, str]]:
    return [{"id": f"{prefix}{n}"} for n in range(count)]


def entities(count: int) -> list[dict[str, object]]:
    return [
        {"name": f"e{n}", "key": "id", "fields": {"id": "uuid"}} for n in range(count)
    ]


DATA_MODEL_PROPS = {
    "entity": [
        {"name": "a", "key": "id", "fields": {"id": "uuid"}, "was": "old"},
        {
            "name": "a",
            "key": "missing",
            "fields": {
                "one": 5,
                "two": {"type": "", "change": "nope", "was": 3},
                "three": {"type": "text", "was": "y"},
            },
            "relations": [{"to": "a"}, {"to": "zzz"}],
        },
        {"name": "c", "key": "k", "fields": {}},
    ]
}
DATA_MODEL_FAULTS = [
    ("entity-duplicate", "entity 'a' is declared more than once"),
    ("change", f"entity[1]: was needs a change ({CHANGE_WORDS})"),
    ("type", "entity[2].fields.one must be a string or a table"),
    ("type", "entity[2].fields.two: 'type' must be a non-empty string"),
    ("change", f"entity[2].fields.two: change must be one of {CHANGE_WORDS}"),
    ("type", "entity[2].fields.two: 'was' must be a non-empty string"),
    ("change", f"entity[2].fields.three: was needs a change ({CHANGE_WORDS})"),
    ("entity-key", "entity[2]: key 'missing' is not a declared field"),
    (
        "relation-target",
        "entity[2].relations[2]: relation target 'zzz' is not an entity",
    ),
    ("type", "entity[3].fields must not be empty"),
    ("entity-key", "entity[3]: key 'k' is not a declared field"),
]
ENDPOINT_PROPS = {
    "path": "orders",
    "was": "x",
    "responses": [
        {"status": 100},
        {"status": 599},
        {"status": 99},
        {"status": 600, "was": "y"},
    ],
}
ENDPOINT_FAULTS = [
    ("type", "endpoint: path must start with '/'"),
    ("change", f"endpoint: was needs a change ({CHANGE_WORDS})"),
    ("type", "'responses[3].status' must be 100-599"),
    ("change", f"responses[4]: was needs a change ({CHANGE_WORDS})"),
    ("type", "'responses[4].status' must be 100-599"),
]
DEPS_PROPS = {
    "edges": {"a#": [], "b": "x", "c": ["d:e"]},
    "status": {"zz": "done", "c": 3, "b": "done", "d:e": "ok"},
}
DEPS_FAULTS = [
    ("type", f"deps.edges: {BAD_NAME}"),
    ("type", "deps.edges.b must be a list of tasks"),
    ("type", f"deps.edges.c: {BAD_NAME}"),
    ("value", "deps.status.zz: task is not in edges"),
    ("type", "deps.status.c must be text"),
]
DIAGRAM_PROPS = {
    "groups": [{"id": "g"}, {"id": "g"}, {"id": "empty"}],
    "nodes": [
        {"id": "n"},
        {"id": "n"},
        {"id": "m", "group": "g"},
        {"id": "k", "group": "nope"},
    ],
    "edges": [{"from": "x", "to": "n"}, {"from": "n", "to": "y"}],
}
DIAGRAM_FAULTS = [
    ("group-duplicate", "diagram: group id 'g' is used more than once"),
    ("node-duplicate", "diagram: node id 'n' is used more than once"),
    ("node-group", "nodes[4]: group 'nope' is not a group id"),
    ("edge-target", "edges[1]: from 'x' is not a node id"),
    ("edge-target", "edges[2]: to 'y' is not a node id"),
    ("group-empty", "diagram: group 'empty' has no nodes"),
]
# 3 groups, 200 nodes and 400 edges are the limits
FULL_DIAGRAM = {
    "groups": ids("g", 3),
    "nodes": [{"id": f"n{n}", "group": f"g{n % 3}"} for n in range(200)],
    "edges": [{"from": "n0", "to": "n1"}] * 400,
}
HUGE_DIAGRAM = {
    "groups": ids("g", 4),
    "nodes": [{"id": f"n{n}", "group": f"g{n % 4}"} for n in range(201)],
    "edges": [{"from": "n0", "to": "n1"}] * 401,
}
HUGE_DIAGRAM_FAULTS = [
    ("too-many", "diagram: at most 3 groups"),
    ("too-many", "diagram: at most 200 nodes"),
    ("too-many", "diagram: at most 400 edges"),
]
TREE_PROPS = {
    "kind": "tree",
    "nodes": [{"id": "a"}, {"id": "b"}, {"id": "c", "group": "nope"}],
    "edges": [
        {"from": "a"},
        {"from": "b"},
        {"from": "a", "to": "c"},
        {"from": "b", "to": "c"},
    ],
}
TREE_FAULTS = [
    ("node-group", "nodes[3]: group 'nope' is not a group id"),
    ("tree-parent", "diagram: tree node 'c' has two parents"),
]
# the walk from `x` enters a cycle that `x` is not part of
CYCLE_PROPS = {
    "kind": "tree",
    "nodes": [{"id": "x"}, {"id": "a"}, {"id": "b"}],
    "edges": [
        {"from": "a", "to": "x"},
        {"from": "b", "to": "a"},
        {"from": "a", "to": "b"},
    ],
}
FLOW_PROPS = {
    "step": [{"id": "a"}, {"id": "a", "next": ["zz"]}, {"id": "b", "next": ["yy"]}]
}
FLOW_FAULTS = [
    ("step-duplicate", "flow: step id 'a' is used more than once"),
    ("step-target", "step[2]: next 'zz' is not a step id"),
    ("step-target", "step[3]: next 'yy' is not a step id"),
]
SEQUENCE_PROPS = {
    "actors": [{"id": "a0"}, *ids("a", 12)],
    "steps": [{"from": "a0", "to": "a1"}, {"from": "zz", "to": "yy"}]
    + [{"from": "a0", "to": "a1"}] * 199,
}
SEQUENCE_FAULTS = [
    ("actor-duplicate", "sequence: actor id 'a0' is used more than once"),
    ("too-many", "sequence: at most 12 actors"),
    ("too-many", "sequence: at most 200 steps"),
    ("step-actor", "steps[2]: from 'zz' is not an actor id"),
    ("step-actor", "steps[2]: to 'yy' is not an actor id"),
]
STATE_PROPS = {
    "states": [{"id": "s0", "kind": "initial"}, {"id": "s0", "kind": "initial"}]
    + ids("t", 39),
    "transitions": [{"from": "zz", "to": "s0"}, {"from": "s0", "to": "yy"}],
}
STATE_FAULTS = [
    ("state-duplicate", "state: state id 's0' is used more than once"),
    ("too-many", "state: at most 40 states"),
    ("two-initial", "state: only one state may be initial"),
    ("transition-state", "transitions[1]: from 'zz' is not a state id"),
    ("transition-state", "transitions[2]: to 'yy' is not a state id"),
]
GRAPH_SIZE_FAULT = (
    "graph-size",
    "data-model: layout graph draws at most 30 entities, this has 31; use layout list",
)


@pytest.mark.parametrize(
    ("component", "props", "expected"),
    [
        pytest.param(
            "data-model", DATA_MODEL_PROPS, DATA_MODEL_FAULTS, id="data-model"
        ),
        pytest.param(
            "data-model",
            {"layout": "graph", "entity": entities(31)},
            [GRAPH_SIZE_FAULT],
            id="data-model-graph-size",
        ),
        pytest.param("endpoint", ENDPOINT_PROPS, ENDPOINT_FAULTS, id="endpoint"),
        pytest.param("deps", DEPS_PROPS, DEPS_FAULTS, id="deps"),
        pytest.param(
            "decision",
            {"options": ["maybe", "maybe", "deny", "deny"]},
            [("option-duplicate", "decision.options: 'deny' is listed twice")],
            id="decision",
        ),
        pytest.param("diagram", DIAGRAM_PROPS, DIAGRAM_FAULTS, id="diagram"),
        pytest.param("diagram", FULL_DIAGRAM, [], id="diagram-at-limits"),
        pytest.param(
            "diagram", HUGE_DIAGRAM, HUGE_DIAGRAM_FAULTS, id="diagram-over-limits"
        ),
        pytest.param("diagram", TREE_PROPS, TREE_FAULTS, id="diagram-tree"),
        pytest.param(
            "diagram",
            CYCLE_PROPS,
            [("tree-cycle", "diagram: tree has a cycle through 'x'")],
            id="diagram-tree-cycle",
            # a cycle walk that stops advancing must fail the test, not hang the run
            marks=pytest.mark.timeout(2, method="signal"),
        ),
        pytest.param("flow", FLOW_PROPS, FLOW_FAULTS, id="flow"),
        pytest.param("sequence", SEQUENCE_PROPS, SEQUENCE_FAULTS, id="sequence"),
        pytest.param("state", STATE_PROPS, STATE_FAULTS, id="state"),
        pytest.param(
            "state",
            {"states": [{"id": "a"}]},
            [("no-initial", "state: one state must have kind initial")],
            id="state-no-initial",
        ),
    ],
)
def test_validator_reports_each_fault(component, props, expected):
    faults = blocks.COMPONENT_SPECS[component].validate(props)
    assert [(f.rule, f.message) for f in faults] == expected
