"""Help text for the component vocabulary, built from the specs."""

from dataclasses import asdict

from varde.pages.blocks.check import COMPONENT_SPECS


def _indented(text: str) -> str:
    return "\n".join(f"  {line}" if line else "" for line in text.rstrip().splitlines())


def type_text(name: str) -> str:
    spec = COMPONENT_SPECS[name]
    fields = "\n".join(f"  {line}" for line in spec.fields)
    return (
        f"{spec.name} - {spec.summary}\n\nFields:\n{fields}\n\n"
        f"Line syntax (in a ```ui fence):\n{_indented(spec.example)}\n"
    )


def index_text() -> str:
    """One line per component; `type_text` gives a component's fields."""
    lines = [
        f"{name} - {COMPONENT_SPECS[name].summary}" for name in sorted(COMPONENT_SPECS)
    ]
    return "\n".join(lines) + "\n\nFields and an example: varde pages blocks <TYPE>\n"


def catalog(names: tuple[str, ...] = ()) -> list[dict[str, object]]:
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
        for spec in (COMPONENT_SPECS[name] for name in names or sorted(COMPONENT_SPECS))
    ]
