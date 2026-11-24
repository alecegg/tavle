"""Props for the data-model `graph` layout.

The drawing is server-laid-out (`er_layout`): entity boxes on a grid with a line per
relation and cardinality labels at both ends, sent as shapes for
`static/components/data-model.js`. It is `aria-hidden`; the relation text list and
the full entity cards below it carry the same facts, and are all a narrow or
printed page shows. Entities are hooked by index (`data-entity`, `data-ends`) so
`static/er.js` can highlight a card's relations without reading any name.
"""

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ..blocks_render.change import (
    GLYPHS,
    change_of,
    copy_line,
    field_props,
    legend_text,
)
from ..blocks_render.common import (
    as_dict,
    as_list,
    count_noun,
)
from ..blocks_render.er_layout import (
    BOX_W,
    HEAD_H,
    ROW_H,
    Box,
    Grid,
    Point,
    label_point,
    place,
    route,
    visible_rows,
)
from ..blocks_render.svg import Shape, el

TEXT_CHARS = 30
ENDS = {
    "one-to-one": ("1", "1"),
    "one-to-many": ("1", "n"),
    "many-to-one": ("n", "1"),
    "many-to-many": ("n", "n"),
}
Entity = Mapping[str, object]


@dataclass(frozen=True)
class Relation:
    source: int
    target: int
    kind: str
    field: str = ""  # set when the relation is inferred from this field

    @property
    def ends(self) -> tuple[str, str]:
        return ENDS.get(self.kind, ("", ""))


def _names(entities: Sequence[Entity]) -> list[str]:
    return [str(e["name"]) for e in entities]


def declared_relations(entities: Sequence[Entity]) -> list[Relation]:
    index = {name: i for i, name in enumerate(_names(entities))}
    return [
        Relation(i, index[str(r["to"])], str(r.get("kind", "")))
        for i, entity in enumerate(entities)
        for r in as_list(entity.get("relations"))
        if str(r["to"]) in index
    ]


def inferred_relations(
    entities: Sequence[Entity], declared: list[Relation]
) -> list[Relation]:
    """A field `<entity>_id` points at that entity unless a relation joins them."""
    folded = {name.casefold(): i for i, name in enumerate(_names(entities))}
    joined = {frozenset((r.source, r.target)) for r in declared}
    found: list[Relation] = []
    for i, entity in enumerate(entities):
        for field in as_dict(entity.get("fields")):
            stem = field[:-3].casefold() if field.casefold().endswith("_id") else ""
            target = folded.get(stem, i)
            pair = frozenset((i, target))
            if target == i or field == entity["key"] or pair in joined:
                continue
            joined.add(pair)
            found.append(Relation(i, target, "many-to-one", field))
    return found


def relation_text(names: list[str], rel: Relation) -> str:
    source, target = names[rel.source], names[rel.target]
    left, right = rel.ends
    middle = f"{left} to {right}" if left else "relates to"
    note = f" (inferred from field {rel.field})" if rel.field else ""
    return f"{source} {middle} {target}{note}"


def _short(text: str) -> str:
    return text if len(text) <= TEXT_CHARS else text[: TEXT_CHARS - 1] + "…"


def _glyph(change: str) -> str:
    return f"{GLYPHS[change]} " if change else ""


def _field_line(name: str, value: object, key: object) -> tuple[str, str]:
    kind, change = (
        (str(value["type"]), str(value.get("change", "")))
        if isinstance(value, Mapping)
        else (str(value), "")
    )
    mark = "* " if name == key else ""
    cls = "vd-er-field" + (f" vd-change-{change}" if change else "")
    cls += " vd-er-keyed" if mark else ""
    return cls, _short(f"{_glyph(change)}{mark}{name}: {kind}")


def _path(points: list[Point]) -> str:
    return "M" + " L".join(f"{x:g} {y:g}" for x, y in points)


def _fk_links(
    index: int, names: list[str], rels: list[Relation]
) -> dict[str, tuple[int, str]]:
    """Field name to `(target entity, its name)` for every `<target>_id` field."""
    found = {}
    for r in rels:
        if r.source == index:
            found[r.field or f"{names[r.target]}_id"] = (r.target, names[r.target])
    return found


def _copy_text(
    entities: Sequence[Entity], names: list[str], rels: list[Relation]
) -> str:
    lines = []
    for entity in entities:
        fields = ", ".join(as_dict(entity.get("fields")))
        change, was = change_of(entity)
        head = f"{entity['name']} (key {entity['key']}): {fields}"
        lines.append(
            head if not change else f"{head} [{copy_line(change, 'entity', was)}]"
        )
    lines += [relation_text(names, r) for r in rels]
    return "\n".join(lines)


def _changes(entities: Sequence[Entity]) -> list[str]:
    found = []
    for entity in entities:
        found.append(change_of(entity)[0])
        found += [
            change_of(v)[0]
            for v in as_dict(entity.get("fields")).values()
            if isinstance(v, Mapping)
        ]
    return [c for c in found if c]


# --- props for the browser (static/components/data-model.js) -------------------


def _text_shape(x: float, y: float, cls: str, body: str) -> Shape:
    return el("text", {"class": cls, "x": f"{x:g}", "y": f"{y:g}"}, body)


def _box_shape(box: Box, entity: Entity) -> Shape:
    change = change_of(entity)[0]
    fields = as_dict(entity.get("fields"))
    shown, hidden = visible_rows(len(fields))
    cls = "vd-er-box" + (f" vd-change-{change}" if change else "")
    rect = {"x": f"{box.x:g}", "y": f"{box.y:g}", "width": f"{BOX_W:g}", "rx": "6"}
    parts = [
        el("rect", {"class": cls, **rect, "height": f"{box.h:g}"}),
        el("rect", {"class": "vd-er-head", **rect, "height": f"{HEAD_H:g}"}),
        _text_shape(
            box.x + 10,
            box.y + 20,
            "vd-er-name",
            _short(_glyph(change) + str(entity["name"])),
        ),
    ]
    for n, (name, value) in enumerate(list(fields.items())[:shown]):
        cls_, body = _field_line(name, value, entity["key"])
        y = box.y + HEAD_H + ROW_H * (n + 0.75)
        parts.append(_text_shape(box.x + 10, y, cls_, body))
    if hidden:
        y = box.y + HEAD_H + ROW_H * (shown + 0.75)
        parts.append(_text_shape(box.x + 10, y, "vd-er-more", f"+{hidden} more"))
    return el("g", {"class": "vd-er-node", "data-entity": str(box.index)}, parts)


def _edge_shape(grid: Grid, rel: Relation, lane: int) -> Shape:
    points = route(grid, grid.boxes[rel.source], grid.boxes[rel.target], lane)
    cls = "vd-er-line" + (" vd-er-inferred" if rel.field else "")
    parts = [el("path", {"class": cls, "d": _path(points)})]
    for at_start, label in zip((True, False), rel.ends, strict=True):
        if label:
            x, y = label_point(points, at_start)
            parts.append(_text_shape(x, y, "vd-er-end", label))
    return el(
        "g", {"class": "vd-er-edge", "data-ends": f"{rel.source} {rel.target}"}, parts
    )


def _card_props(
    index: int, entity: Entity, names: list[str], rels: list[Relation]
) -> dict[str, object]:
    change, was = change_of(entity)
    links = _fk_links(index, names, rels)
    key = entity["key"]
    fields = []
    for name, value in as_dict(entity.get("fields")).items():
        field = field_props(name, value, key)
        target = links.get(name)
        field["fk"] = (
            None if target is None else {"target": target[0], "name": target[1]}
        )
        fields.append(field)
    return {
        "index": index,
        "name": str(entity["name"]),
        "change": change,
        "was": was,
        "fields": fields,
    }


def graph_props(data: dict[str, object]) -> dict[str, object]:
    entities = as_list(data["entity"])
    names = _names(entities)
    digest = hashlib.sha1(  # mollify: ignore[weak-hash] id, not security
        "\0".join(names).encode(), usedforsecurity=False
    ).hexdigest()[:8]
    declared = declared_relations(entities)
    rels = declared + inferred_relations(entities, declared)
    grid = place([len(as_dict(e.get("fields"))) for e in entities])
    shapes = [_edge_shape(grid, r, lane) for lane, r in enumerate(rels)]
    shapes += [_box_shape(b, e) for b, e in zip(grid.boxes, entities, strict=True)]
    changes = _changes(entities)
    summary = (
        f"{count_noun(len(entities), 'entity', 'entities')}, "
        f"{count_noun(len(rels), 'relation', 'relations')}"
    )
    return {
        "layout": "graph",
        "digest": digest,
        "summary": summary,
        "legend": legend_text(changes) if changes else "",
        "copy": _copy_text(entities, names, rels),
        "drawing": {
            "box": f"0 0 {grid.width:g} {grid.height:g}",
            "width": f"{grid.width:g}",
            "height": f"{grid.height:g}",
            "shapes": shapes,
        },
        "relations": [
            {"text": relation_text(names, r), "ends": f"{r.source} {r.target}"}
            for r in rels
        ],
        "entities": [_card_props(i, e, names, rels) for i, e in enumerate(entities)],
    }
