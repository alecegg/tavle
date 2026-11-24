"""Help text and JSON catalog for the component vocabulary, built from the specs."""

from collections.abc import Mapping
from dataclasses import asdict

from varde.ui.blocks.spec import BlockSpec, PropertySpec


def _indented(text: str, depth: int = 1) -> str:
    pad = "  " * depth
    return "\n".join(
        f"{pad}{line}" if line else "" for line in text.rstrip().splitlines()
    )


def _type_label(prop: PropertySpec) -> str:
    label = f"list of {prop.items}" if prop.items else prop.type
    label = f"{label}, nonempty" if prop.nonempty else label
    return f"{label}: {' | '.join(prop.enum)}" if prop.enum else label


def _property_lines(rows: list[tuple[str, PropertySpec]]) -> list[str]:
    """One line per (label, property), nested properties indented below their parent."""
    width = max(len(label) for label, _ in rows)
    lines: list[str] = []
    for label, prop in rows:
        need = "required" if prop.required else "optional"
        lines.append(f"{label.ljust(width)}  {need}  {_type_label(prop)}")
        if prop.fields:
            nested = _property_lines([(p.name, p) for p in prop.fields])
            lines += [f"  {line}" for line in nested]
    return lines


def _field_lines(specs: Mapping[str, BlockSpec], name: str) -> list[str]:
    """The generated field lines of a component: its properties, then any extra key."""
    spec = specs[name]
    rows = [(prop.name, prop) for prop in spec.properties]
    if spec.extra_keys:
        rows.append((f"<{spec.extra_keys.name}>", spec.extra_keys))
    return _property_lines(rows) if rows else []


def type_text(specs: Mapping[str, BlockSpec], name: str) -> str:
    spec = specs[name]
    sections = [f"{spec.name} - {spec.summary}"]
    if spec.properties or spec.extra_keys:
        sections.append("Fields:\n" + _indented("\n".join(_field_lines(specs, name))))
    if spec.notes:
        sections.append("Details:\n" + _indented("\n".join(spec.notes)))
    sections.append(f"Line syntax (in a ```ui fence):\n{_indented(spec.example)}")
    return "\n\n".join(sections) + "\n"


def index_text(specs: Mapping[str, BlockSpec]) -> str:
    """One line per component; `type_text` gives a component's fields."""
    lines = [f"{name} - {specs[name].summary}" for name in sorted(specs)]
    return "\n".join(lines) + "\n\nFields and an example: varde pages blocks <TYPE>\n"


def catalog(
    specs: Mapping[str, BlockSpec], names: tuple[str, ...] = ()
) -> list[dict[str, object]]:
    """The metadata of the named components (all when none is named), as plain data.

    Each entry holds name, summary, block_type, properties and extra_keys; a
    property holds name, type, required, enum, items, fields (nested properties)
    and nonempty.
    """
    return [
        {
            "name": spec.name,
            "summary": spec.summary,
            "block_type": spec.block_type,
            "properties": [asdict(prop) for prop in spec.properties],
            "extra_keys": asdict(spec.extra_keys) if spec.extra_keys else None,
        }
        for spec in (specs[name] for name in names or sorted(specs))
    ]
