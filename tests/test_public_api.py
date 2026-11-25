"""The page API named in design D3 is exported from the `tavle` package."""

from __future__ import annotations

import pytest

import tavle

FUNCTIONS = [
    # page
    "assemble_static",
    "render_fragment",
    "check",
    "quality_warnings",
    "page_theme",
    "doc_theme",
    "ThemeLayers",
    "no_layers",
    "catalog_text",
    "preset_values",
    "resolved_values",
    "theme_catalog",
    "values_text",
    "answer_schema",
    "parse_interval",
    # comments
    "append_comment",
    "append_status",
    "append_reply",
    "fold",
    "read_rows",
    "mark_latest_decisions",
    "target_anchor",
    "anchor_slug",
    "comments_path",
    "watch_lines",
    # serve
    "serve",
    "new_token",
    "host_allowed",
    "origin_allowed",
    "token_matches",
    "is_json_type",
    "write_event_stream",
    "watch_files",
    "classify_host",
    "bind_error_message",
    "parse_json_object",
    "strings",
    # listings
    "comment_text",
    "filtered_comments",
    "finding_row",
    "block_rows",
    "parse_port",
]

CLASSES = ["PageServer", "Broadcaster"]

CONSTANTS = [
    "PAGE_SPECS",
    "KINDS",
    "LOOPBACK",
    "MAX_BODY",
    "MAX_STREAMS",
    "SECURITY_HEADERS",
    "TOKEN_HEADER",
]


@pytest.mark.parametrize("name", FUNCTIONS)
def test_function_is_exported_and_callable(name: str) -> None:
    assert callable(getattr(tavle, name))


@pytest.mark.parametrize("name", CLASSES)
def test_class_is_exported(name: str) -> None:
    assert isinstance(getattr(tavle, name), type)


@pytest.mark.parametrize("name", CONSTANTS)
def test_constant_is_exported(name: str) -> None:
    value = getattr(tavle, name)
    assert name.isupper()
    assert not callable(value)
