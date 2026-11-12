"""Props and answer schemas for `choice`, `form` and `comment`.

The widgets render in the browser (`static/components/{choice,form,comment}.js`);
`static/recap.js` hydrates them through `data-component` and the whitelisted
`data-props` JSON and posts one `answer` row. Option values and field names are
the only strings the client sends back, and the server checks them again.
"""

from varde_pages.blocks.inputs import option_label_value
from varde_pages.blocks.spec import AnswerSchema
from varde_pages.blocks_render.common import as_dict, as_list

Props = dict[str, object]
MAX_NOTE = 8000  # the server's cap on an answer's text


def _hint(field: dict) -> str:
    """The limit a reader can act on: text length or number range (else empty)."""
    if field["type"] == "text" and "maxlength" in field:
        return f"Up to {field['maxlength']} characters."
    if field["type"] != "number":
        return ""
    low, high = field.get("min"), field.get("max")
    if low is not None and high is not None:
        return f"From {low} to {high}."
    if low is not None:
        return f"At least {low}."
    return f"At most {high}." if high is not None else ""


def _client_field(field: dict) -> dict[str, object]:
    """The keys the client needs to read a field back (a whitelist, not the table)."""
    keys = ("name", "type", "required", "min", "max")
    return {k: field[k] for k in keys if k in field}


def choice_props(data: Props) -> Props:
    """What the browser draws a `choice` from: each option as label, value, detail."""
    options = []
    for option in as_list(data.get("options")):
        label, value = option_label_value(option)
        detail = as_dict(option).get("detail")
        options.append(
            {
                "label": label,
                "value": value,
                "detail": str(detail) if detail else "",
                "recommended": as_dict(option).get("recommended") is True,
            }
        )
    return {
        "question": data["question"],
        "options": options,
        "multiple": data.get("multiple") is True,
        "comment": data.get("comment") is True,
        "maxNote": MAX_NOTE,
    }


def _field_props(field: dict) -> Props:
    """One form field as the browser draws it; `client` is what it reads back."""
    shown: Props = {
        "name": field["name"],
        "label": field["label"],
        "type": field["type"],
        "required": field.get("required") is True,
        "hint": _hint(field),
        "client": _client_field(field),
    }
    for key in ("min", "max"):
        if key in field:
            shown[key + "Text"] = str(field[key])
    if field["type"] == "text":
        shown["limit"] = field.get("maxlength", 600)
    if field["type"] == "select":
        shown["options"] = [str(o) for o in as_list(field["options"])]
    return shown


def form_props(data: Props) -> Props:
    fields = [as_dict(f) for f in as_list(data.get("fields"))]
    return {
        "title": str(data["title"]) if data.get("title") else "",
        "submit": str(data.get("submit", "Submit")),
        "fields": [_field_props(f) for f in fields],
    }


def comment_props(data: Props) -> Props:
    return {
        "label": str(data["label"]),
        "submit": str(data.get("submit", "Send")),
        "maxNote": MAX_NOTE,
    }


def choice_values(data: Props) -> tuple[str, ...]:
    """The answer value of each option, in order."""
    return tuple(option_label_value(o)[1] for o in as_list(data.get("options")))


def choice_answer_schema(data: Props) -> AnswerSchema:
    kind = "list" if data.get("multiple") is True else "string"
    fields = ("text",) if data.get("comment") is True else ()
    return AnswerSchema(kind, fields, choice_values(data))


def form_answer_schema(data: Props) -> AnswerSchema:
    return AnswerSchema(
        "form", (), (), tuple(as_dict(f) for f in as_list(data.get("fields")))
    )


def comment_answer_schema(data: Props) -> AnswerSchema:
    """The value is the fixed verdict `commented`; the reader's text is the answer."""
    return AnswerSchema("verdict", ("text",), ("commented",))
