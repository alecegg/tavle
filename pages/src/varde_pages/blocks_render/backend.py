"""Props for the data-model and endpoint blocks, drawn by `static/components/`.

The server sorts out the change vocabulary, summaries and Copy text; the browser
builds the cards and tables.
"""

from collections.abc import Mapping

from varde_pages.blocks_render.change import (
    change_of,
    copy_line,
    field_props,
    legend_text,
)
from varde_pages.blocks_render.common import as_dict, as_list, count_noun
from varde_pages.blocks_render.er import graph_props

# One changed row: (change, name used in the Copy text, was).
Changed = list[tuple[str, str, str]]


def _fields_props(
    items: Mapping[str, object], scope: str, mark_key: object, changed: Changed
) -> list[dict[str, object]]:
    rows = [field_props(str(n), v, mark_key) for n, v in items.items()]
    for name, value in items.items():
        change, was = change_of(value) if isinstance(value, Mapping) else ("", "")
        if change:
            changed.append((change, f"{scope}.{name}", was))
    return rows


def _changes_props(changed: Changed, summary: str) -> dict[str, object]:
    """`summary`, plus the Copy text and legend line a block with changes carries."""
    if not changed:
        return {"summary": summary, "legend": "", "copy": None}
    kinds = [c for c, _, _ in changed]
    copy = "\n".join(copy_line(*c) for c in changed)
    return {"summary": summary, "legend": legend_text(kinds), "copy": copy}


def _entity_props(entity: dict[str, object], changed: Changed) -> dict[str, object]:
    change, was = change_of(entity)
    name = str(entity["name"])
    if change:
        changed.append((change, name, was))
    return {
        "name": name,
        "change": change,
        "was": was,
        "fields": _fields_props(
            as_dict(entity.get("fields")), name, entity["key"], changed
        ),
        "relations": [
            {"to": str(r["to"]), "kind": str(r.get("kind", "relation"))}
            for r in as_list(entity.get("relations"))
        ],
    }


def data_model_props(data: dict[str, object]) -> dict[str, object]:
    if data.get("layout") == "graph":
        return graph_props(data)
    changed: Changed = []
    entities = [_entity_props(e, changed) for e in as_list(data["entity"])]
    relations = sum(len(e["relations"]) for e in entities)  # type: ignore[arg-type]
    summary = (
        f"{count_noun(len(entities), 'entity', 'entities')}, "
        f"{count_noun(relations, 'relation', 'relations')}"
    )
    return {"layout": "list", "entities": entities, **_changes_props(changed, summary)}


def endpoint_props(data: dict[str, object]) -> dict[str, object]:
    changed: Changed = []
    change, was = change_of(data)
    if change:
        changed.append((change, f"{data['method']} {data['path']}", was))
    request = data.get("request")
    rows = (
        _fields_props(request, "request", None, changed)
        if isinstance(request, dict) and request
        else None
    )
    responses = []
    for r in as_list(data["responses"]):
        r_change, r_was = change_of(r)
        if r_change:
            changed.append((r_change, f"response {r['status']}", r_was))
        responses.append(
            {
                "status": str(r["status"]),
                "body": str(r.get("body", "")),
                "change": r_change,
                "was": r_was,
            }
        )
    auth = str(data["auth"])
    summary = f"{data['method']} {data['path']}: auth {auth}, "
    summary += count_noun(len(responses), "response", "responses")
    return {
        "method": str(data["method"]),
        "path": str(data["path"]),
        "auth": auth,
        "change": change,
        "was": was,
        "note": str(data["summary"]) if "summary" in data else None,
        "request": rows,
        "responses": responses,
        **_changes_props(changed, summary),
    }
