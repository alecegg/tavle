"""The data-model graph layout: placement, routing, relation text, inference, faults."""

from __future__ import annotations

import re
from itertools import pairwise
from pathlib import Path
from typing import Any

import pytest

from varde.pages.page_check import PAGE_SPECS
from varde.pages.render import render_page
from varde.ui.blocks import check_props, type_text
from varde.ui.blocks.backend import validate_data_model
from varde.ui.blocks_render import render_block
from varde.ui.blocks_render.backend import data_model_props
from varde.ui.blocks_render.er import (
    declared_relations,
    inferred_relations,
    relation_text,
)
from varde.ui.blocks_render.er_layout import (
    BOX_W,
    edges_cross_boxes,
    place,
    route,
)

FIXTURES = Path(__file__).parent / "fixtures" / "widgets"
JSON_PROPS = re.compile(r'<script type="application/json">.*?</script>', re.DOTALL)
HOSTILE = '<img src=x onerror=alert(1)> "q" &amp; <script>alert(1)</script>'


def entity(name: str, /, *relations: tuple[str, str], **fields: Any) -> dict[str, Any]:
    out: dict[str, Any] = {
        "name": name,
        "key": "id",
        "fields": {"id": "uuid", **fields},
    }
    if relations:
        out["relations"] = [{"to": to, "kind": kind} for to, kind in relations]
    return out


def model(*entities: dict[str, Any], **extra: object) -> dict[str, object]:
    return {"entity": list(entities), **extra}


def test_list_props_are_unchanged_by_the_list_layout() -> None:
    data = model(entity("a", ("b", "one-to-many")), entity("b", name="text"))
    plain = data_model_props(data)
    assert data_model_props({**data, "layout": "list"}) == plain
    assert plain["layout"] == "list" and "drawing" not in plain


def test_placement_is_deterministic_and_grid_shaped() -> None:
    counts = [2, 9, 1, 3, 4, 0, 2]
    assert place(counts) == place(counts)
    grid = place(counts)
    assert grid.cols == 3 and len(grid.row_top) == 3
    cells = [(b.col, b.grid_row) for b in grid.boxes[:4]]
    assert cells == [(0, 0), (1, 0), (2, 0), (0, 1)]
    taller = grid.boxes[1].h
    assert taller > grid.boxes[0].h
    assert grid.row_bottom[0] - grid.row_top[0] == taller


def on_edge(point: tuple[float, float], box: Any) -> bool:
    x, y = point
    inside_x = box.x <= x <= box.x + BOX_W
    inside_y = box.y <= y <= box.bottom
    touches = x in (box.x, box.x + BOX_W) or y in (box.y, box.bottom)
    return inside_x and inside_y and touches


@pytest.mark.parametrize("count", [2, 3, 5, 9, 30])
def test_lines_touch_card_edges_and_cross_no_card(count: int) -> None:
    grid = place([2 + i % 8 for i in range(count)])
    for lane, (i, j) in enumerate(
        (i, j) for i in range(count) for j in range(count) if (i * 7 + j) % 5 == 0
    ):
        a, b = grid.boxes[i], grid.boxes[j]
        points = route(grid, a, b, lane)
        assert on_edge(points[0], a) and on_edge(points[-1], b), (i, j, points)
        assert all((x0 == x1 or y0 == y1) for (x0, y0), (x1, y1) in pairwise(points))
        assert not edges_cross_boxes(grid, points), (i, j, points)
        assert all(0 <= x <= grid.width and 0 <= y <= grid.height for x, y in points)


def test_self_relation_is_a_loop_on_one_edge() -> None:
    grid = place([3])
    box = grid.boxes[0]
    points = route(grid, box, box, 0)
    assert len(points) == 4
    assert on_edge(points[0], box) and on_edge(points[-1], box)


def graph(*entities: dict[str, Any]) -> dict[str, Any]:
    return data_model_props(model(*entities, layout="graph"))


def shape_texts(shapes: list[Any]) -> list[str]:
    """Every text body in the drawing's shapes, in order."""
    found: list[str] = []
    for _tag, _attrs, content in shapes:
        if isinstance(content, str):
            found.append(content)
        elif content:
            found += shape_texts(content)
    return found


def classes(shapes: list[Any]) -> list[str]:
    found: list[str] = []
    for _tag, attrs, content in shapes:
        found.append(attrs.get("class", ""))
        found += classes(content) if isinstance(content, list) else []
    return found


def test_text_list_matches_the_relations() -> None:
    props = graph(
        entity("order", ("customer", "many-to-one"), ("order", "one-to-many")),
        entity("customer", ("order", "one-to-one"), ("order", "many-to-many")),
    )
    assert [r["text"] for r in props["relations"]] == [
        "order n to 1 customer",
        "order 1 to n order",
        "customer 1 to 1 order",
        "customer n to n order",
    ]
    assert classes(props["drawing"]["shapes"]).count("vd-er-edge") == 4


def test_relation_without_cardinality_reads_relates_to() -> None:
    names = ["a", "b"]
    rel = declared_relations([{"name": "a", "relations": [{"to": "b"}]}, {"name": "b"}])
    assert relation_text(names, rel[0]) == "a relates to b"


def test_relations_are_inferred_from_id_fields_only_when_undeclared() -> None:
    entities = [
        entity("customer"),
        entity("order", ("customer", "many-to-one"), customer_id="uuid"),
        entity("line", order_id="uuid", Customer_ID="uuid", parent_id="uuid"),
    ]
    declared = declared_relations(entities)
    inferred = inferred_relations(entities, declared)
    assert [(r.source, r.target, r.field) for r in inferred] == [
        (2, 1, "order_id"),
        (2, 0, "Customer_ID"),
    ]
    props = graph(*entities)
    texts = [r["text"] for r in props["relations"]]
    assert "line n to 1 order (inferred from field order_id)" in texts
    assert classes(props["drawing"]["shapes"]).count("vd-er-line vd-er-inferred") == 2


def test_foreign_key_fields_name_the_target_entity() -> None:
    props = graph(
        entity("customer"),
        entity("order", ("customer", "many-to-one"), customer_id="uuid"),
    )
    fk = {f["name"]: f["fk"] for f in props["entities"][1]["fields"]}
    assert fk["customer_id"] == {"target": 0, "name": "customer"}
    assert fk["id"] is None


def test_changes_survive_in_graph() -> None:
    data = model(
        {
            **entity("a", total={"type": "int", "change": "modified", "was": "text"}),
            "change": "added",
        },
        entity("b"),
        layout="graph",
    )
    props: Any = data_model_props(data)
    assert props["entities"][0]["change"] == "added"
    texts = shape_texts(props["drawing"]["shapes"])
    assert "+ a" in texts and "~ total: int" in texts
    assert props["legend"] == "Changes: 1 added, 1 modified"


def test_hostile_text_stays_out_of_the_markup() -> None:
    data = model(entity(HOSTILE, (HOSTILE, "one-to-one"), **{HOSTILE: HOSTILE}))
    host = render_block("data-model", {**data, "layout": "graph"}, None, 1)
    markup = JSON_PROPS.sub("", host)
    assert HOSTILE not in host and "<script" not in markup and "<img" not in markup
    assert "style=" not in markup and "onclick" not in markup


def test_many_fields_show_a_more_row_and_cards_list_all() -> None:
    props = graph(entity("wide", **{f"f{i}": "t" for i in range(200)}))
    assert "+195 more" in shape_texts(props["drawing"]["shapes"])
    assert len(props["entities"][0]["fields"]) == 201


def test_thirty_entities_pass_and_thirty_one_fault() -> None:
    def names(n: int) -> list[dict[str, Any]]:
        return [entity(f"e{i}", (f"e{(i + 1) % n}", "one-to-many")) for i in range(n)]

    ok = validate_data_model(model(*names(30), layout="graph"))
    assert ok == []
    faults = validate_data_model(model(*names(31), layout="graph"))
    assert [f.rule for f in faults] == ["graph-size"]
    assert validate_data_model(model(*names(31))) == []


def test_unknown_layout_and_unknown_entity_fault() -> None:
    ring = check_props("data-model", model(entity("a"), layout="ring"), 1)
    assert [e.rule for e in ring] == ["type"]  # the layout enum is a property
    bad = model(entity("a", ("ghost", "one-to-one")), layout="graph")
    assert [f.rule for f in validate_data_model(bad)] == ["relation-target"]


def test_props_are_deterministic() -> None:
    data = model(
        entity("a", ("b", "one-to-many")), entity("b", a_id="uuid"), layout="graph"
    )
    assert data_model_props(data) == data_model_props(data)


@pytest.mark.parametrize("name", ["rich-er.md", "rich-er-stress.md"])
def test_fixtures_render_without_error(name: str) -> None:
    body = render_page((FIXTURES / name).read_text(), name).body
    assert "vb-error" not in body and '"layout": "graph"' in body
    assert "<script" not in JSON_PROPS.sub("", body) and "style=" not in body


def test_help_text_lists_the_layout_prop() -> None:
    text = type_text(PAGE_SPECS, "data-model")
    assert "layout" in text and "graph" in text
