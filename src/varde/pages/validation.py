"""Shared text, size and JSON input rules for page writes."""

import json
from typing import Any, cast

MAX_QUOTE = 200


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
