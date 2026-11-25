from pathlib import Path

from varde.pages.theme.page import doc_theme, no_layers
from varde.ui import parse_toml


def test_caller_layers_and_front_matter(tmp_path: Path) -> None:
    doc = tmp_path / "page.md"
    layer = parse_toml('preset = "harbor"', "caller")

    def layers(_doc: Path):
        return [(layer, "caller")]

    themed = doc_theme(doc, "# Page", layers)
    default = doc_theme(doc, "# Page", no_layers)
    overridden = doc_theme(doc, "---\ntheme: varde\n---\n# Page", layers)
    assert themed.tokens != default.tokens
    assert overridden.tokens == default.tokens
