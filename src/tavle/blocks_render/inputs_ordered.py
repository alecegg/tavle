"""Props and answer schemas for `ranking` and `slider`.

Same contract as `blocks_render.inputs`: the widgets render in the browser
(`static/components/{ranking,slider}.js`), `static/inputs_ordered.js` hydrates
them and posts one `answer` row, and the server checks that row again. A ranking
sends the item values in order; a slider sends one number.
"""

from ..blocks.inputs import option_label_value
from ..blocks.inputs_ordered import slider_bounds
from ..blocks.spec import AnswerSchema
from ..blocks_render.common import as_dict, as_list

Props = dict[str, object]


MAX_TICKS = 20  # tick marks only when the scale has at most this many steps


def ranking_props(data: Props) -> Props:
    """Items as label, value, detail and the name that tells twins apart."""
    items = []
    for item in as_list(data.get("items")):
        label, value = option_label_value(item)
        detail = as_dict(item).get("detail")
        items.append(
            {
                "label": label,
                "value": value,
                "detail": str(detail) if detail else "",
                "name": label if value == label else f"{label} ({value})",
            }
        )
    return {"question": data["question"], "items": items}


def _tick_count(low: float, high: float, step: float) -> int:
    """Tick marks along the track, or 0 when the scale is irregular or too long."""
    count = (high - low) / step
    if abs(count - round(count)) > 1e-9 or count > MAX_TICKS:
        return 0
    return round(count) + 1


def slider_props(data: Props) -> Props:
    """The numbers (as the client reads them), their text, the end labels and ticks."""
    low, high, step = slider_bounds(data)
    ends = [str(e) for e in as_list(data.get("labels"))] or [str(low), str(high)]
    return {
        "label": data["label"],
        "min": low,
        "max": high,
        "step": step,
        "minText": str(low),
        "maxText": str(high),
        "stepText": str(step),
        "ends": ends,
        "ticks": _tick_count(low, high, step),
    }


def ranking_answer_schema(data: Props) -> AnswerSchema:
    values = tuple(option_label_value(i)[1] for i in as_list(data.get("items")))
    return AnswerSchema("ranking", (), values)


def slider_answer_schema(data: Props) -> AnswerSchema:
    return AnswerSchema("number", (), (), bounds=slider_bounds(data))
