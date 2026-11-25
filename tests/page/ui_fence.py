"""Test helpers: write props (a TOML body or a spec example) as a `ui` fence."""

import json
import re
import tomllib

from tavle.blocks_render.registry import COMPONENTS
from tavle.components import mount_block

# Keep control and bidi characters visible within a single statement line.
_LINE_BREAKS = re.compile(
    r"[\x0b\x0c\x1c-\x1e\x7f-\x9f\u2028\u2029\u202a-\u202e\u2066-\u2069]"
)


def statement_text(block_id: str, component: str, props: dict[str, object]) -> str:
    """Write a statement with one JSON-encoded prop per line."""
    lines = []
    for key, value in props.items():
        text = json.dumps(value, ensure_ascii=False)
        text = _LINE_BREAKS.sub(lambda m: f"\\u{ord(m.group()):04x}", text)
        lines.append(f"  {key}: {text},")
    return f"{block_id} = {component}(\n" + "\n".join(lines) + "\n)"


def toml_props(body: str) -> dict[str, object]:
    return tomllib.loads(body)


def example_fence(statement: str) -> str:
    """A `ui` fence holding a spec's example statement."""
    return f"```ui\n{statement}\n```\n"


def ui_fence(component: str, toml_body: str, block_id: str = "b1") -> str:
    """A `ui` fence holding one statement built from TOML props."""
    statement = statement_text(block_id, component, toml_props(toml_body))
    return f"```ui id={block_id}\n{statement}\n```\n"


def block_host(name: str, props: dict[str, object], block_id: str = "w") -> str:
    """The mount host the page renderer writes for a client-side block."""
    prepare = COMPONENTS[name].props
    assert prepare is not None
    return mount_block(name, prepare(props), "", block_id)
