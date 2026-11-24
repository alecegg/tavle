"""Block types for data and interfaces: data-model, endpoint."""

from varde.pages.blocks.change import (
    CHANGE_NOTES,
    CHANGE_PROPERTIES,
    CHANGES,
    change_rule_faults,
)
from varde.pages.blocks.er import LAYOUT_NOTE, LAYOUTS, layout_faults
from varde.pages.blocks.rules import Fault, check_keys, duplicates, str_field, tables
from varde.pages.blocks.spec import BlockSpec, PropertySpec

_RELATION_KINDS = ("one-to-one", "one-to-many", "many-to-one", "many-to-many")
_CHANGE_NOTE = (
    "Change markers, optional on an entity, field, endpoint, parameter or response:",
    *(f"  {line}" for line in CHANGE_NOTES),
)
_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")


def _typed_item_faults(item: dict[str, object], where: str) -> list[Fault]:
    """One `{type, change, was}` table inside a field or parameter map.

    The properties cannot name a map's own keys, so this checks the item whole.
    """
    faults = check_keys(item, {"type"}, {"change", "was"}, where)
    faults += str_field(item, "type", where)
    if "change" in item and item["change"] not in CHANGES:
        faults.append(
            Fault("change", f"{where}: change must be one of {', '.join(CHANGES)}")
        )
    return faults + str_field(item, "was", where) + change_rule_faults(item, where)


def _typed_map_faults(value: object, where: str) -> list[Fault]:
    """A table of `name: type text` or `name: {type, change, was}`."""
    if not isinstance(value, dict):
        return []  # the properties report it
    if not value:
        return [Fault("type", f"{where} must not be empty")]
    faults: list[Fault] = []
    for name, item in value.items():
        if isinstance(item, str):
            continue
        if not isinstance(item, dict):
            faults.append(Fault("type", f"{where}.{name} must be a string or a table"))
            continue
        faults += _typed_item_faults(item, f"{where}.{name}")
    return faults


def _relation_faults(
    relation: dict[str, object], names: set[str], where: str
) -> list[Fault]:
    target = relation.get("to")
    if isinstance(target, str) and target.strip() and target not in names:
        return [
            Fault(
                "relation-target",
                f"{where}: relation target '{target}' is not an entity",
            )
        ]
    return []


def _entity_faults(
    entity: dict[str, object], names: set[str], where: str
) -> list[Fault]:
    faults = _typed_map_faults(entity.get("fields"), f"{where}.fields")
    faults += change_rule_faults(entity, where)
    key = entity.get("key")
    fields = entity.get("fields")
    if isinstance(key, str) and isinstance(fields, dict) and key not in fields:
        faults.append(
            Fault("entity-key", f"{where}: key '{key}' is not a declared field")
        )
    for n, relation in enumerate(tables(entity, "relations", where), 1):
        faults += _relation_faults(relation, names, f"{where}.relations[{n}]")
    return faults


def validate_data_model(data: dict[str, object]) -> list[Fault]:
    faults = layout_faults(data)
    entities = tables(data, "entity", "data-model")
    named = [n for e in entities if isinstance(n := e.get("name"), str)]
    faults += [
        Fault("entity-duplicate", f"entity '{name}' is declared more than once")
        for name in duplicates(named)
    ]
    for n, entity in enumerate(entities, 1):
        faults += _entity_faults(entity, set(named), f"entity[{n}]")
    return faults


def _route_faults(data: dict[str, object]) -> list[Fault]:
    path = data.get("path")
    if isinstance(path, str) and path.strip() and not path.startswith("/"):
        return [Fault("type", "endpoint: path must start with '/'")]
    return []


def _out_of_range(status: object) -> bool:
    """An integer status outside 100-599; other types are the properties' fault."""
    if not isinstance(status, int) or isinstance(status, bool):
        return False
    return not 100 <= status <= 599


def _response_faults(response: dict[str, object], where: str) -> list[Fault]:
    faults = change_rule_faults(response, where)
    if _out_of_range(response.get("status")):
        faults.append(Fault("type", f"'{where}.status' must be 100-599"))
    return faults


def validate_endpoint(data: dict[str, object]) -> list[Fault]:
    faults = _route_faults(data) + change_rule_faults(data, "endpoint")
    faults += _typed_map_faults(data.get("request"), "endpoint.request")
    for n, response in enumerate(tables(data, "responses", "endpoint"), 1):
        faults += _response_faults(response, f"responses[{n}]")
    return faults


DATA_MODEL = BlockSpec(
    "data-model",
    "Entities with a key and relations to other entities",
    (
        "entity: one per entity; name is unique; key names the field that identifies",
        "  a row and must be in fields; fields maps a field name to a type text, or",
        "  to {type, change, was}; relations.to names another entity in this block.",
        *LAYOUT_NOTE,
        *_CHANGE_NOTE,
    ),
    r"""data-model = data-model(
  entity: [
    {"name": "customer", "key": "id", "fields": {"id": "uuid", "email": "text"}},
    {
      "name": "order",
      "key": "id",
      "fields": {"id": "uuid", "customer_id": "uuid", "total": "cents"},
      "relations": [{"to": "customer", "kind": "many-to-one"}]
    },
  ],
)
""",
    validate_data_model,
    properties=(
        PropertySpec(
            "entity",
            "list",
            required=True,
            nonempty=True,
            items="object",
            fields=(
                PropertySpec("name", "string", required=True, nonempty=True),
                PropertySpec("key", "string", required=True, nonempty=True),
                PropertySpec("fields", "object", required=True),
                PropertySpec(
                    "relations",
                    "list",
                    nonempty=True,
                    items="object",
                    fields=(
                        PropertySpec("to", "string", required=True, nonempty=True),
                        PropertySpec(
                            "kind", "string", required=True, enum=_RELATION_KINDS
                        ),
                    ),
                ),
                *CHANGE_PROPERTIES,
            ),
        ),
        PropertySpec("layout", "string", enum=LAYOUTS),
    ),
)

ENDPOINT = BlockSpec(
    "endpoint",
    "One HTTP endpoint with its auth rule and responses",
    (
        "path: starts with /.",
        'auth: required; "none" must be written to mean public.',
        "summary: one line.",
        "request: maps a parameter to a type text, or to {type, change, was}.",
        "responses: status is 100-599.",
        *_CHANGE_NOTE,
    ),
    r"""endpoint = endpoint(
  method: "POST",
  path: "/orders",
  auth: "bearer",
  summary: "Create an order",
  request: {"customer_id": "uuid", "total": "cents"},
  responses: [
    {"status": 201, "body": "the new order"},
    {"status": 422, "body": "validation errors"},
  ],
)
""",
    validate_endpoint,
    properties=(
        PropertySpec("method", "string", required=True, enum=_METHODS),
        PropertySpec("path", "string", required=True, nonempty=True),
        PropertySpec("auth", "string", required=True, nonempty=True),
        PropertySpec("summary", "string", nonempty=True),
        PropertySpec("request", "object"),
        PropertySpec(
            "responses",
            "list",
            required=True,
            nonempty=True,
            items="object",
            fields=(
                PropertySpec("status", "integer", required=True),
                PropertySpec("body", "string", nonempty=True),
                *CHANGE_PROPERTIES,
            ),
        ),
        *CHANGE_PROPERTIES,
    ),
)
