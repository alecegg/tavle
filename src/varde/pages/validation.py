"""Shared text, size and JSON input rules for page writes."""

import json
import re
from typing import Any, cast

MAX_TEXT = 8000
MAX_ITEM = 600
MAX_QUOTE = 200
# C0 and C1 controls (tab, newline, return allowed), NUL, bidi overrides and isolates.
CONTROLS = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069]")


def parse_json_object(raw: bytes) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("body is not valid JSON") from error
    if not isinstance(data, dict):
        raise ValueError("body must be a JSON object")  # noqa: TRY004
    return data


def strings(data: dict[str, Any], *names: str) -> list[str]:
    values = [data.get(name) for name in names]
    if not all(isinstance(value, str) for value in values):
        raise ValueError(f"{' and '.join(names)} must be strings")
    return cast("list[str]", values)
