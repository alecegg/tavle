"""Every spec but a page statement has a component file; no block has a renderer."""

from pathlib import Path

from varde_pages.blocks import COMPONENT_SPECS
from varde_pages.blocks_render.registry import COMPONENTS, PAGE_STATEMENTS
from varde_pages.components import component_bundle

COMPONENT_FILES = Path(__file__).parents[1] / "src/varde_pages/static/components"


def test_component_registry_matches_the_specs() -> None:
    assert set(COMPONENTS) == set(COMPONENT_SPECS)


def test_each_block_has_a_component_file_and_only_page_statements_do_not() -> None:
    files = {path.stem for path in COMPONENT_FILES.glob("*.js")} - {"mount", "shared"}
    assert files == set(COMPONENT_SPECS) - PAGE_STATEMENTS
    assert 'components["tabs"]' in component_bundle()


def test_the_registry_has_no_html_renderer() -> None:
    assert not any(hasattr(entry, "render") for entry in COMPONENTS.values())
