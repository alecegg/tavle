"""Client-side blocks: a host element with props, and the one script that mounts them.

`static/components/<name>.js` exports `view(m, props)`; `mount.js` exports
`mountComponents`. The bundle is Mithril, every component and a boot call as one
classic script, so a served page and a standalone export load the same code.
"""

import html
import json
import re
from collections.abc import Callable
from importlib.resources import files

from varde.pages.template import HOST_ATTR, page_shell

_STATIC = files("varde.pages").joinpath("static")
_EXPORT = re.compile(r"^export ", re.MULTILINE)
_IMPORT = re.compile(r"^import\s", re.MULTILINE)
_EXPORT_FORM = re.compile(r"^export (?!(function|const|class)\b)", re.MULTILINE)
_EXPORTED = re.compile(r"^export (?:function|const|class) (\w+)", re.MULTILINE)
_BOOT = """\
const run = () => mountComponents(document, window.m, components);
const loading = document.readyState === 'loading';
if (loading) document.addEventListener('DOMContentLoaded', run);
else run();
// app.js swaps blocks on live updates; mount the new hosts.
new MutationObserver(run).observe(document, { childList: true, subtree: true });
"""


_HOST = re.compile(
    rf'(<div {HOST_ATTR}="(?P<name>[\w-]+)"[^>]*>.*?<script type="application/json">)'
    r"(?P<payload>.*?)(</script>)",
    re.DOTALL,
)


def _payload(props: dict[str, object]) -> str:
    return json.dumps(props, ensure_ascii=False).replace("<", "\\u003c")


def host_props(markup: str, name: str) -> list[dict[str, object]]:
    """Props of every `name` host in `markup`, nested ones included."""
    if f'{HOST_ATTR}="{name}"' not in markup:
        return []
    return [
        json.loads(found["payload"])
        for found in _HOST.finditer(markup)
        if found["name"] == name
    ]


def map_host_props(
    markup: str, name: str, change: Callable[[dict[str, object]], dict[str, object]]
) -> str:
    """`markup` with each `name` host's props replaced by `change(props)`."""

    if f'{HOST_ATTR}="{name}"' not in markup:
        return markup

    def swap(found: re.Match[str]) -> str:
        if found["name"] != name:
            return found[0]
        props = change(json.loads(found["payload"]))
        return f"{found[1]}{_payload(props)}{found[4]}"

    return _HOST.sub(swap, markup)


def mount_block(
    name: str,
    props: dict[str, object],
    fallback: str,
    block_id: str | None = None,
    copy: str | None = None,
    held: str = "",
) -> str:
    """Host for component `name`; `fallback` is the text shown with no script.

    `copy` is the block's plain text for a container or the action menu to read
    before the component has mounted (`data-copy`, as the drawn block carries it);
    a block with no copy text of its own copies its `fallback` source. `held` is
    markup placed inside the host after its props (a container's held blocks).
    """
    payload = _payload(props)
    owner = "" if block_id is None else f' data-block-id="{html.escape(block_id)}"'
    owner += f' data-copy="{html.escape(fallback if copy is None else copy)}"'
    return (
        f'<div {HOST_ATTR}="{html.escape(name)}"{owner}>'
        f'<noscript><pre class="vd-noscript">{html.escape(fallback)}</pre></noscript>'
        f'<script type="application/json">{payload}</script>'
        f"{held}</div>"
    )


def _scoped(source: str, result: str) -> str:
    """The module body as an expression: `export` dropped, `result` returned."""
    if _IMPORT.search(source):
        raise ValueError("a component file must not import")
    if _EXPORT_FORM.search(source):
        raise ValueError("a component file may only export declarations")
    return f"(() => {{\n{_EXPORT.sub('', source)}\nreturn {result};\n}})()"


def _module(source: str) -> str:
    """A component file as an expression: an object of everything it exports."""
    return _scoped(source, "{ " + ", ".join(_EXPORTED.findall(source)) + " }")


def component_bundle() -> str:
    """Mithril, all components and the boot call as one classic script."""
    components = _STATIC.joinpath("components")
    names = sorted(
        entry.name.removesuffix(".js")
        for entry in components.iterdir()
        if entry.name.endswith(".js") and entry.name != "mount.js"
    )
    mount = components.joinpath("mount.js").read_text(encoding="utf-8")
    parts = [
        _STATIC.joinpath("vendor", "mithril.js").read_text(encoding="utf-8"),
        "(() => {\nconst components = {};",
        *(
            f"components[{json.dumps(name)}] = "
            + _module(components.joinpath(f"{name}.js").read_text(encoding="utf-8"))
            + ";"
            for name in names
        ),
        "globalThis.vardeComponents = components; // read by dashboard views",
        f"const mountComponents = {_scoped(mount, 'mountComponents')};",
        "globalThis.vardeMountComponents = mountComponents; // shadow-root hosts",
        _BOOT + "})();",
    ]
    return "\n".join(parts)


def export_page(title: str, main: str) -> str:
    """Self-contained page: stylesheet inline, and the bundle when a block needs it."""
    if f"{HOST_ATTR}=" not in main:
        return page_shell(title, main, None)
    bundle = component_bundle()
    if "</script" in bundle.lower():
        raise ValueError("the component bundle must not contain a closing script tag")
    return page_shell(title, f"{main}<script>{bundle}</script>", None)
