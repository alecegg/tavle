"""Components `choice`, `form` and `comment`: props checks and form-value checks.

These are line-syntax components (a `ui` fence); none has a TOML fence form. The
renderers and answer schemas live in `blocks_render.inputs`. Pure functions.
"""

import math
import re

from varde.pages.blocks.rules import Fault, check_keys, duplicates, is_number
from varde.pages.blocks.spec import BlockSpec, PropertySpec
from varde.pages.validation import CONTROLS, MAX_ITEM

MAX_OPTIONS = 50
MAX_FIELDS = 30
MAX_LABEL = 200
MAX_DETAIL = 1000
MAX_VALUE_JSON = 8000  # longest JSON text of one answer value
MAX_VALUE = 600  # an option value or a text field's longest allowed answer
FIELD_TYPES = ("text", "number", "select", "checkbox")
FIELD_NAME = re.compile(r"^[a-z][a-z0-9_-]{0,47}$")
_TYPE_KEYS = {
    "text": {"maxlength"},
    "number": {"min", "max"},
    "select": {"options"},
    "checkbox": set(),
}
ALL_TYPE_KEYS = set().union(*_TYPE_KEYS.values())

# Properties shared by the input widgets: `inputs_ordered` reuses them.
QUESTION = PropertySpec("question", "string", required=True, nonempty=True)
LABEL = PropertySpec("label", "string", required=True, nonempty=True)
SUBMIT = PropertySpec("submit", "string", nonempty=True)


def option_list(name: str) -> PropertySpec:
    """Options are a string or a table (so `any`); limits are checked in code."""
    return PropertySpec(name, "list", required=True, items="any", nonempty=True)


MAX_LIST = 100


def _members_ok(kind: str, members: object) -> bool:
    if not isinstance(members, list) or len(members) > MAX_LIST:
        return False
    if kind != "list":
        return True
    return bool(members) and len(set(map(str, members))) == len(
        members
    )  # a picked set: each once


def allowed_value(kind: str, value: object, allowed: tuple[str, ...]) -> bool:
    members = value if kind == "list" else [value]
    if not _members_ok(kind, members):
        return False
    if not allowed:
        return all(isinstance(m, str) and len(m) <= MAX_ITEM for m in members)  # type: ignore[union-attr]
    return all(isinstance(m, str) and m in allowed for m in members)  # type: ignore[union-attr]


def finite(value: object) -> bool:
    """True for a real number (not a bool) that is neither NaN nor infinite."""
    if not is_number(value):
        return False
    try:
        return math.isfinite(value)  # type: ignore[arg-type]
    except OverflowError:
        return False


def limit_fault(value: object, where: str, limit: int) -> list[Fault]:
    """A fault for a non-blank string over `limit` or holding controls.

    Other values are left to the property metadata, which reports them once.
    """
    if not isinstance(value, str) or not value.strip():
        return []
    if len(value) > limit or CONTROLS.search(value):
        return [
            Fault("type", f"{where} must be at most {limit} characters, no controls")
        ]
    return []


def text_fault(value: object, where: str, limit: int) -> list[Fault]:
    """A fault unless `value` is a non-empty string within `limit`, no controls."""
    if not isinstance(value, str) or not value.strip():
        return [Fault("type", f"{where} must be a non-empty string")]
    return limit_fault(value, where, limit)


def option_label_value(option: object) -> tuple[str, str]:
    """(label, value) of a validated option: a string, or a table with a label."""
    if isinstance(option, dict):
        label = str(option.get("label", ""))
        return label, str(option.get("value", label))
    return str(option), str(option)


def option_faults(option: object, where: str) -> list[Fault]:
    """Faults of one option, which takes two shapes (so the metadata says `any`)."""
    if isinstance(option, str):
        return text_fault(option, where, MAX_VALUE)
    if not isinstance(option, dict):
        return [Fault("type", f"{where} must be a string or a table with a label")]
    faults = check_keys(option, {"label"}, {"detail", "value", "recommended"}, where)
    faults += text_fault(option.get("label"), f"{where}.label", MAX_LABEL)
    if "recommended" in option and not isinstance(option["recommended"], bool):
        faults.append(Fault("type", f"{where}.recommended must be true or false"))
    for key, limit in (("detail", MAX_DETAIL), ("value", MAX_VALUE)):
        if key in option:
            faults += text_fault(option[key], f"{where}.{key}", limit)
    return faults


def _options_faults(data: dict[str, object]) -> list[Fault]:
    options = data.get("options")
    if not isinstance(options, list) or not options:
        return []  # the metadata reports a missing, mistyped or empty list
    if len(options) > MAX_OPTIONS:
        return [Fault("type", f"choice.options must be a list of 1-{MAX_OPTIONS}")]
    faults: list[Fault] = []
    for index, option in enumerate(options, start=1):
        faults += option_faults(option, f"choice.options[{index}]")
    return faults or _option_set_faults(options)


def _option_set_faults(options: list[object]) -> list[Fault]:
    values = [option_label_value(o)[1] for o in options]
    faults = [
        Fault("option-duplicate", f"choice.options: value '{v}' is listed twice")
        for v in duplicates(values)
    ]
    marked = [o for o in options if isinstance(o, dict) and o.get("recommended")]
    if len(marked) > 1:
        faults.append(
            Fault(
                "recommended-many", "choice.options: at most one option is recommended"
            )
        )
    return faults


def validate_choice(data: dict[str, object]) -> list[Fault]:
    return _options_faults(data)


def no_faults(data: dict[str, object]) -> list[Fault]:
    """For a widget whose properties say everything its props must satisfy."""
    return []


def _maxlength(field: dict[str, object]) -> int | None:
    """The field's maxlength when it is a whole number, else None."""
    value = field.get("maxlength")
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _maxlength_faults(field: dict[str, object], where: str) -> list[Fault]:
    value = _maxlength(field)  # a wrong type is the metadata's to report
    if value is None or 1 <= value <= MAX_VALUE:
        return []
    return [Fault("type", f"{where}.maxlength must be a whole number 1-{MAX_VALUE}")]


def _bound_faults(field: dict[str, object], where: str) -> list[Fault]:
    bounds = {k: field[k] for k in ("min", "max") if is_number(field.get(k))}
    faults = [
        Fault("type", f"{where}.{key} must be a finite number")
        for key, value in bounds.items()
        if not finite(value)
    ]
    if faults or len(bounds) < len(("min", "max")):
        return faults
    if bounds["min"] > bounds["max"]:  # type: ignore[operator]
        faults.append(Fault("range", f"{where}: min is above max"))
    return faults


def _select_faults(field: dict[str, object], where: str) -> list[Fault]:
    if "options" not in field:
        return [Fault("missing-key", f"{where}: select needs 'options'")]
    options = field["options"]
    if not isinstance(options, list) or not options:
        return []  # the metadata reports a mistyped or empty list
    if len(options) > MAX_OPTIONS:
        return [Fault("type", f"{where}.options must be a list of 1-{MAX_OPTIONS}")]
    names = [o for o in options if isinstance(o, str)]
    faults: list[Fault] = []
    for name in names:
        faults += text_fault(name, f"{where}.options", MAX_VALUE)
    return faults + [
        Fault("option-duplicate", f"{where}.options: '{o}' is listed twice")
        for o in duplicates(names)
    ]


def _misplaced_key_faults(
    field: dict[str, object], kind: str, where: str
) -> list[Fault]:
    """Keys the metadata allows on some field type but not on this one."""
    misplaced = (ALL_TYPE_KEYS & field.keys()) - _TYPE_KEYS[kind]
    return [
        Fault("unknown-key", f"{where}: unknown key '{k}'") for k in sorted(misplaced)
    ]


def _name_faults(name: object, where: str) -> list[Fault]:
    if not isinstance(name, str) or not name.strip() or FIELD_NAME.match(name):
        return []  # a wrong type or blank name is the metadata's to report
    return [Fault("type", f"{where}.name must match {FIELD_NAME.pattern}")]


def _field_faults(field: object, index: int) -> list[Fault]:
    where = f"form.fields[{index}]"
    kind = field.get("type") if isinstance(field, dict) else None
    if not isinstance(field, dict) or kind not in FIELD_TYPES:
        return []  # the metadata reports a non-table or an unknown type
    faults = _misplaced_key_faults(field, kind, where)
    faults += limit_fault(field.get("label"), f"{where}.label", MAX_LABEL)
    faults += _name_faults(field.get("name"), where)
    if kind == "text":
        faults += _maxlength_faults(field, where)
    if kind == "number":
        faults += _bound_faults(field, where)
    if kind == "select":
        faults += _select_faults(field, where)
    return faults


def _field_json_bound(field: dict[str, object]) -> int:
    """Most JSON characters one field's value can take: quotes, escapes, key."""
    kind = field.get("type")
    if kind == "text":
        longest = _maxlength(field) or MAX_VALUE
    elif kind == "select":
        options = field.get("options")
        names = options if isinstance(options, list) else []
        longest = max((len(o) for o in names if isinstance(o, str)), default=0)
    else:
        longest = 0
    return (
        2 * longest + len(str(field.get("name", ""))) + 40
    )  # 40: number or bool, glue


def _size_faults(fields: list[object]) -> list[Fault]:
    rows = [f for f in fields if isinstance(f, dict)]
    bound = sum(_field_json_bound(f) for f in rows)
    if bound <= MAX_VALUE_JSON:
        return []
    return [
        Fault(
            "size",
            f"form: fields can add up to {bound} characters of answer; "
            f"the limit is {MAX_VALUE_JSON} (lower maxlength or drop fields)",
        )
    ]


def _fields_faults(fields: object) -> list[Fault]:
    if not isinstance(fields, list) or not fields:
        return []  # the metadata reports a missing, mistyped or empty list
    if len(fields) > MAX_FIELDS:
        return [Fault("type", f"form.fields must be a list of 1-{MAX_FIELDS}")]
    faults: list[Fault] = []
    for index, field in enumerate(fields, start=1):
        faults += _field_faults(field, index)
    names = [f["name"] for f in fields if isinstance(f, dict) and "name" in f]
    faults += _size_faults(fields)
    return faults + [
        Fault("field-duplicate", f"form.fields: name '{n}' is used twice")
        for n in duplicates([n for n in names if isinstance(n, str)])
    ]


def validate_form(data: dict[str, object]) -> list[Fault]:
    return _fields_faults(data.get("fields"))


def _text_value(field: dict[str, object], value: object) -> None:
    limit = int(field.get("maxlength", MAX_VALUE))  # type: ignore[call-overload]
    if not isinstance(value, str) or len(value) > limit or CONTROLS.search(value):
        raise ValueError(
            f"field {field['name']!r} must be text up to {limit} characters"
        )
    if field.get("required") and not value.strip():
        raise ValueError(f"field {field['name']!r} is required")


def _number_value(field: dict[str, object], value: object) -> None:
    name = field["name"]
    if value is None and not field.get("required"):
        return
    if not finite(value):
        raise ValueError(f"field {name!r} must be a finite number")
    low, high = field.get("min"), field.get("max")
    if is_number(low) and value < low:  # type: ignore[operator]
        raise ValueError(f"field {name!r} is below {low}")
    if is_number(high) and value > high:  # type: ignore[operator]
        raise ValueError(f"field {name!r} is above {high}")


def _select_value(field: dict[str, object], got: object) -> None:
    if got == "" and not field.get("required"):
        return  # the blank first option of an optional select
    if got not in field["options"]:  # type: ignore[operator]
        raise ValueError(f"field {field['name']!r} must be one of its options")


def _checkbox_value(field: dict[str, object], got: object) -> None:
    if isinstance(got, bool):
        if field.get("required") and not got:
            raise ValueError(f"field {field['name']!r} is required")
        return
    raise ValueError(f"field {field['name']!r} must be true or false")


_VALUE_CHECKS = {
    "text": _text_value,
    "number": _number_value,
    "select": _select_value,
    "checkbox": _checkbox_value,
}


def check_form_value(fields: tuple[dict[str, object], ...], value: object) -> None:
    """Raise ValueError unless `value` holds exactly the form's fields, each valid."""
    if not isinstance(value, dict):
        raise ValueError("form value must be an object")  # noqa: TRY004
    names = {str(f["name"]) for f in fields}
    if set(value) != names:
        raise ValueError("form value must hold exactly the form's fields")
    for field in fields:
        check = _VALUE_CHECKS.get(str(field["type"]))
        if check:
            check(field, value[str(field["name"])])


CHOICE = BlockSpec(
    "choice",
    "A question answered by picking one option, or several",
    (
        "question  required text",
        "options   required list: a string, or a table (label, detail, value)",
        "          recommended: true on one table shows a Recommended badge",
        "multiple  optional true to allow several picks; default one",
        "comment   optional true to add a free-text box",
    ),
    r"""choice = choice(
  question: "Which database?",
  comment: true,
  options: [
    {"label": "SQLite", "detail": "No server, one file", "recommended": true},
    {"label": "Postgres", "detail": "Shared server", "value": "postgres"},
  ],
)
""",
    validate_choice,
    block_type="widget",
    properties=(
        QUESTION,
        option_list("options"),
        PropertySpec("multiple", "boolean"),
        PropertySpec("comment", "boolean"),
    ),
)

FORM = BlockSpec(
    "form",
    "Several fields (text, number, select, checkbox) sent with one submit",
    (
        "title    optional text",
        "submit   optional button label; default Submit",
        "fields: list of {name, label, type, ...}; type text|number|select|checkbox",
        "  required  optional true; a checkbox must then be ticked",
        "  maxlength  text only, up to 600",
        "  min, max   number only, finite bounds",
        "  options    select only, list of text; a blank choice comes first",
    ),
    r"""form = form(
  title: "Rollout settings",
  submit: "Save",
  fields: [
    {"name": "owner", "label": "Owner", "type": "text", "required": true,
     "maxlength": 40},
    {"name": "replicas", "label": "Replicas", "type": "number", "min": 1, "max": 10},
    {"name": "region", "label": "Region", "type": "select", "options": ["eu", "us"]},
    {"name": "notify", "label": "Notify the team", "type": "checkbox"},
  ],
)
""",
    validate_form,
    block_type="widget",
    properties=(
        PropertySpec("title", "string", nonempty=True),
        SUBMIT,
        PropertySpec(
            "fields",
            "list",
            required=True,
            items="object",
            nonempty=True,
            fields=(
                PropertySpec("name", "string", required=True, nonempty=True),
                LABEL,
                PropertySpec("type", "string", required=True, enum=FIELD_TYPES),
                PropertySpec("required", "boolean"),
                PropertySpec("maxlength", "integer"),
                PropertySpec("min", "number"),
                PropertySpec("max", "number"),
                PropertySpec("options", "list", items="string", nonempty=True),
            ),
        ),
    ),
)

COMMENT = BlockSpec(
    "comment",
    "A free-text box whose text is stored as the page's answer",
    (
        "label   required text shown above the box",
        "submit  optional button label; default Send",
    ),
    r"""comment = comment(
  label: "Anything we missed?",
  submit: "Send",
)
""",
    no_faults,
    block_type="widget",
    properties=(LABEL, SUBMIT),
)
