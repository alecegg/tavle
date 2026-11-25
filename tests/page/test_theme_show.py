import json

from tavle import (
    TOKENS,
    catalog_text,
    doc_theme,
    preset_values,
    resolved_values,
    theme_catalog,
    values_text,
)


def _resolve_theme(doc, frontmatter=None):
    text = (
        "---\n"
        + "\n".join(f"{k}: {v}" for k, v in (frontmatter or {}).items())
        + "\n---\n"
    )
    return doc_theme(doc, text)


def test_listing():
    catalog = theme_catalog()
    text = catalog_text(catalog)
    data = json.loads(json.dumps(catalog))
    assert len(text.encode()) < 2048
    assert set(data["tokens"]) == {token.name for token in TOKENS}
    assert all(f"{name}:" in text for name in data["tokens"])
    assert all(name in text for name in data["presets"])


def test_preset_reports_same_tokens():
    values = preset_values("harbor")
    text = values_text(values)
    assert all(
        f"{scope}.{name}:" in text for scope, items in values.items() for name in items
    )


def test_resolved_sources(tmp_path):
    theme = _resolve_theme(tmp_path / "page.md", {"theme.accent": "#0055aa"})
    values = resolved_values(theme)
    text = values_text(values)
    data = json.loads(json.dumps(values))
    assert data["light"]["accent"]["source"] == "front matter"
    assert "light.accent: #0055aa (front matter)" in text
    assert all(
        f"{scope}.{name}:" in text and item["source"] in text
        for scope, items in data.items()
        for name, item in items.items()
    )
