"""Props for the file-tree component (`static/components/file-tree.js`).

`fold` turns the flat path list into a nested structure and the component draws it.
Single-child folder chains show as one row (`a/b/c`). A file whose path matches the
title of a `code` block links to it: once the page knows its blocks,
`link_file_trees` adds `links` (path to element id) to each file-tree host.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from ..blocks_render.change import (
    GLYPHS,
    change_of,
)
from ..blocks_render.common import as_list
from ..components import host_props, map_host_props

Entry = Mapping[str, object]


@dataclass
class Folder:
    name: str
    path: str
    folders: dict[str, Folder] = field(default_factory=dict)
    files: dict[str, Entry] = field(default_factory=dict)

    def count(self) -> int:
        return len(self.files) + sum(f.count() for f in self.folders.values())


def fold(entries: Sequence[Entry]) -> Folder:
    """Nest the flat `path` list. A path that appears twice is a fault (ValueError)."""
    root = Folder("", "")
    for entry in entries:
        *dirs, leaf = str(entry["path"]).split("/")
        folder = root
        for name in dirs:
            if name in folder.files:
                raise ValueError(f"'{folder.path}/{name}' is both a file and a folder")
            path = f"{folder.path}/{name}" if folder.path else name
            folder = folder.folders.setdefault(name, Folder(name, path))
        if leaf in folder.files or leaf in folder.folders:
            raise ValueError(f"path '{entry['path']}' appears more than once")
        folder.files[leaf] = entry
    return root


def _ordered(items: Mapping[str, object]) -> list[str]:
    return sorted(items, key=lambda name: (name.casefold(), name))


def compact(folder: Folder) -> Folder:
    """Follow a chain of folders that each hold only one folder; keep its name."""
    names = [folder.name]
    while len(folder.folders) == 1 and not folder.files:
        folder = next(iter(folder.folders.values()))
        names.append(folder.name)
    return Folder("/".join(names), folder.path, folder.folders, folder.files)


def summary_text(entries: Sequence[Entry]) -> str:
    """`5 files: 2 added, 1 modified, 2 unchanged`; the parts add up to the files."""
    changes = [change_of(e)[0] for e in entries]
    parts = [f"{changes.count(c)} {c}" for c in GLYPHS if c in changes]
    if "" in changes:
        parts.append(f"{changes.count('')} unchanged")
    noun = "file" if len(entries) == 1 else "files"
    return f"{len(entries)} {noun}: {', '.join(parts)}"


def _label(entry: Entry) -> str:
    change, was = change_of(entry)
    text = f"{change} " if change else ""
    text += str(entry["path"])
    text += f" (was {was})" if was else ""
    text += f" ({entry['role']})" if entry.get("role") else ""
    return text + (f": {entry['note']}" if entry.get("note") else "")


def copy_text(folder: Folder, indent: int = 0) -> str:
    """An indented plain list: `name/` for folders, `<glyph> name` for changed files."""
    lines: list[str] = []
    pad = "  " * indent
    for name in _ordered(folder.folders):
        lines.append(f"{pad}{name}/")
        lines.append(copy_text(folder.folders[name], indent + 1))
    for name in _ordered(folder.files):
        change, was = change_of(folder.files[name])
        glyph = f"{GLYPHS[change]} " if change else ""
        lines.append(f"{pad}{glyph}{name}{f' (was {was})' if was else ''}")
    return "\n".join(line for line in lines if line)


def match_target(path: str, titles: Mapping[str, str]) -> str:
    """The anchor of the code block whose title is the path or a trailing part of it."""
    if path in titles:
        return titles[path]
    tails = [t for t in titles if path.endswith("/" + t)]
    return titles[max(tails, key=len)] if tails else ""


def target_id(anchor: str) -> str:
    """The DOM id a linked block gets."""
    return f"blk-{anchor}"


def _file_props(leaf: str, entry: Entry) -> dict[str, object]:
    change, was = change_of(entry)
    return {
        "name": leaf,
        "path": str(entry["path"]),
        "change": change,
        "was": was,
        "role": entry.get("role") or "",
        "note": entry.get("note") or "",
        "label": _label(entry),
    }


def _folder_props(folder: Folder) -> dict[str, object]:
    shown = compact(folder)
    return {
        "name": shown.name,
        "path": shown.path,
        "count": shown.count(),
        "folders": [_folder_props(shown.folders[n]) for n in _ordered(shown.folders)],
        "files": [_file_props(n, shown.files[n]) for n in _ordered(shown.files)],
    }


def file_tree_props(data: dict[str, object]) -> dict[str, object]:
    """What the `file-tree` component draws: the folded, ordered tree and its texts."""
    entries = as_list(data["entries"])
    root = fold(entries)
    raw_collapse = data.get("collapse")
    title = str(data.get("title", ""))
    summary = summary_text(entries)
    return {
        "title": title,
        "summary": summary,
        "collapse": raw_collapse if isinstance(raw_collapse, int) else None,
        "copy": "\n".join(filter(None, [title, summary, copy_text(root)])),
        "folders": [_folder_props(root.folders[n]) for n in _ordered(root.folders)],
        "files": [_file_props(n, root.files[n]) for n in _ordered(root.files)],
    }


def file_links(paths: Sequence[str], titles: Mapping[str, str]) -> dict[str, str]:
    """Element id of the code block each path links to; others are left out."""
    found = {path: match_target(path, titles) for path in paths}
    return {path: target_id(anchor) for path, anchor in found.items() if anchor}


def code_titles(markup: str) -> list[str]:
    """The titles of the `code` blocks in one block's HTML, as authored."""
    return [
        str(props["title"])
        for props in host_props(markup, "code")
        if props.get("title")
    ]


def link_file_trees(markup: str, titles: Mapping[str, str]) -> str:
    """Give each file-tree host in `markup` the `links` to the code blocks it names."""

    def linked(props: dict[str, object]) -> dict[str, object]:
        links = file_links(_paths(props), titles)
        return {**props, "links": links} if links else props

    return map_host_props(markup, "file-tree", linked)


def _paths(node: Mapping[str, object]) -> list[str]:
    """Every file path under a props tree node."""
    files = [str(file["path"]) for file in as_list(node.get("files"))]
    folders = as_list(node.get("folders"))
    return files + [path for folder in folders for path in _paths(folder)]
