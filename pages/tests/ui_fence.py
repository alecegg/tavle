"""Test helpers: write props (a TOML body or a spec example) as a `ui` fence."""

import tomllib

from varde_pages.blocks.statement import statement_text
from varde_pages.blocks_render.registry import COMPONENTS
from varde_pages.components import mount_block


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
