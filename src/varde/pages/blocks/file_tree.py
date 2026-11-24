"""Block type for changed files: file-tree."""

from varde.pages.blocks.change import (
    CHANGE_FIELDS,
    CHANGE_PROPERTIES,
    change_rule_faults,
)
from varde.pages.blocks.rules import Fault, duplicates, tables
from varde.pages.blocks.spec import BlockSpec, PropertySpec


def path_faults(path: object, where: str) -> list[Fault]:
    """A path is `a/b/c`: no empty, `.` or `..` part, no leading or trailing slash."""
    if not isinstance(path, str) or not path.strip():
        return []  # absent, or a fault the properties already report
    if any(part in ("", ".", "..") for part in path.split("/")):
        return [
            Fault(
                "path",
                f"{where}: path '{path}' needs plain segments "
                "(no leading or trailing slash, empty, '.' or '..' part)",
            )
        ]
    return []


def _folder_faults(paths: list[str]) -> list[Fault]:
    """A file and a folder cannot share a path (`a` and `a/b`)."""
    folders = {
        "/".join(p.split("/")[:n]) for p in paths for n in range(1, len(p.split("/")))
    }
    return [
        Fault("path", f"file-tree: '{p}' is both a file and a folder")
        for p in sorted(set(paths) & folders)
    ]


def _entry_faults(entry: dict[str, object], where: str) -> list[Fault]:
    faults = path_faults(entry["path"], where) if "path" in entry else []
    return faults + change_rule_faults(entry, where)


def _collapse_faults(data: dict[str, object]) -> list[Fault]:
    collapse = data.get("collapse")
    if not isinstance(collapse, int) or isinstance(collapse, bool) or collapse >= 0:
        return []
    return [Fault("type", "file-tree: 'collapse' must be a whole number, 0 or more")]


def validate_file_tree(data: dict[str, object]) -> list[Fault]:
    faults = _collapse_faults(data)
    entries = tables(data, "entries", "file-tree")
    for n, entry in enumerate(entries, 1):
        faults += _entry_faults(entry, f"file-tree.entries[{n}]")
    paths = [str(e["path"]) for e in entries if isinstance(e.get("path"), str)]
    faults += [
        Fault("duplicate-path", f"file-tree: path '{p}' appears more than once")
        for p in duplicates(paths)
    ]
    return faults + _folder_faults(paths)


FILE_TREE = BlockSpec(
    "file-tree",
    "Changed files as a folder tree with change markers, notes and link to code",
    (
        "title     optional heading",
        "entries   list of tables, one per file; a path appears once",
        "  path    `dir/file.ext`, no leading slash",
        "  note    optional short text shown on the same row",
        "  role    optional label such as test or config",
        *(f"  {line}" for line in CHANGE_FIELDS),
        "          a renamed file sits at its new path; `was` is the old path",
        "collapse  optional: close folders deeper than this many levels (default none)",
        "A file whose path ends with the title of a `code` block links to that block.",
    ),
    r"""file-tree = file-tree(
  title: "Changed files",
  collapse: 2,
  entries: [
    {"path": "src/queue.py", "change": "modified", "note": "push returns the id"},
    {"path": "src/retry.py", "change": "added"},
    {"path": "src/backoff.py", "change": "renamed", "was": "src/wait.py"},
    {"path": "tests/test_queue.py", "change": "modified", "role": "test"},
  ],
)
""",
    validate_file_tree,
    properties=(
        PropertySpec("title", "string", nonempty=True),
        PropertySpec("collapse", "integer"),
        PropertySpec(
            "entries",
            "list",
            required=True,
            nonempty=True,
            items="object",
            fields=(
                PropertySpec("path", "string", required=True, nonempty=True),
                PropertySpec("note", "string", nonempty=True),
                PropertySpec("role", "string", nonempty=True),
                *CHANGE_PROPERTIES,
            ),
        ),
    ),
)
