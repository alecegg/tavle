"""First-party HTML for the components; invalid blocks render an error card."""

from ..blocks import SPECS, check_props
from ..blocks_render.common import card, esc
from ..blocks_render.registry import COMPONENTS, Component
from ..components import mount_block


def error_card(title: str, lines: list[str]) -> str:
    items = "".join(f"<li>{esc(line)}</li>" for line in lines)
    return (
        '<div class="vb">'
        + card(esc(title), f"<ul>{items}</ul>", "vb-error")
        + "</div>"
    )


def errors_card(name: str, lines: list[str]) -> str:
    """`error_card` titled "<name> block has N error(s)"."""
    return error_card(
        f"{name} block has {len(lines)} error{'s' * (len(lines) != 1)}", lines
    )


def mount_client_block(
    component: str, shown: dict[str, object], source: str, block_id: str | None
) -> str:
    """Host for props already prepared for the browser; a `copy` prop is `data-copy`."""
    copy = shown.get("copy")
    return mount_block(
        component, shown, source, block_id, copy if isinstance(copy, str) else None
    )


def render_block(
    component: str,
    props: dict[str, object],
    block_id: str | None,
    line: int,
    source: str = "",
) -> str:
    """HTML for one statement's props; `line` is its document line, for errors.

    The block becomes a mount host whose `<noscript>` shows `source`.
    """
    errors = [e.text() for e in check_props(component, props, line)]
    if errors:
        return errors_card(component, errors)
    data = {key: value for key, value in props.items() if key != "covers"}
    entry = COMPONENTS[component]
    shown = data if entry.props is None else entry.props(data)
    return mount_client_block(component, shown, source, block_id)


__all__ = [
    "COMPONENTS",
    "SPECS",
    "Component",
    "error_card",
    "errors_card",
    "mount_client_block",
    "render_block",
]
