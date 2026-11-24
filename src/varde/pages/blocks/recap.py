"""Component `recap`: a plan-to-change recap; props are the recap's JSON keys."""

from varde.pages.blocks.rules import Fault
from varde.pages.blocks.spec import BlockSpec, PropertySpec


def validate_recap(data: dict[str, object]) -> list[Fault]:
    return []


RECAP = BlockSpec(
    "recap",
    "A plan's changed files, drift flags and review buttons",
    (
        "rows      list of changed files: file, status, hunk (and optional",
        "          tasks, blocks, drift, added, removed, shared, binary, truncated)",
        "plan, base, head  optional text for the heading",
        "summary   optional {name: count}",
        "untouched, unverified  optional drift lists",
    ),
    r"""recap = recap(
  plan: "demo",
  base: "main",
  head: "work",
  summary: {"modified": 1},
  rows: [
    {"file": "a.py", "status": "modified", "hunk": "@@ -1 +1 @@", "tasks": ["t1"]},
  ],
)
""",
    validate_recap,
    block_type="status",
    properties=(
        PropertySpec("plan", "string"),
        PropertySpec("base", "string"),
        PropertySpec("head", "string"),
        PropertySpec("summary", "object"),
        PropertySpec(
            "rows",
            "list",
            required=True,
            items="object",
            fields=(
                PropertySpec("file", "string", required=True),
                PropertySpec("status", "string", required=True),
                PropertySpec("hunk", "string", required=True),
                PropertySpec("old_file", "any"),  # a path, or null for no rename
                PropertySpec("tasks", "list", items="string"),
                PropertySpec("blocks", "list", items="string"),
                PropertySpec("drift", "list", items="string"),
                PropertySpec("added", "list"),
                PropertySpec("removed", "list"),
                PropertySpec("shared", "boolean"),
                PropertySpec("binary", "boolean"),
                PropertySpec("truncated", "boolean"),
            ),
        ),
        PropertySpec(
            "untouched",
            "list",
            items="object",
            fields=(
                PropertySpec("task", "string"),
                PropertySpec("owns", "string"),
            ),
        ),
        PropertySpec("unverified", "list", items="string"),
    ),
)
