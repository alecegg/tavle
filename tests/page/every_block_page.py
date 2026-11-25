"""Build a page with every block example for export and theme tests."""

import base64
from pathlib import Path

from tavle import PAGE_SPECS, make_read_only
from tavle.page.assemble import include_ctx
from tavle.page.render import render_page

PIXEL = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def every_block_page(root: Path) -> str:
    """The exported body of a page holding each block type's spec example.

    The examples hold each other by id (the tabs hold `code`), the `include` names a
    plan beside the page, and the `image` names a file under `img/`.
    """
    (root / "img").mkdir(exist_ok=True)
    (root / "img" / "login-screen.png").write_bytes(PIXEL)
    (root / "plan.md").write_text(
        "# Plan\n\n## Acceptance criteria\n\n- works\n", "utf-8"
    )
    fences = (f"```ui\n{spec.example.strip()}\n```\n" for spec in PAGE_SPECS.values())
    doc = root / "all.md"
    doc.write_text("# Every block\n\n" + "\n".join(fences), encoding="utf-8")
    text = doc.read_text(encoding="utf-8")
    page = render_page(text, doc.name, include_ctx(text, doc, export=True)[0])
    return make_read_only(page.body)
