"""Vendored scripts and token CSS served from the library static folder."""

from __future__ import annotations

import pytest

from varde.ui.shell import token_css, vendor_asset


def test_vendor_asset_returns_mithril() -> None:
    assert b"m" in vendor_asset("mithril.js")
    assert len(vendor_asset("mithril.js")) > 1000


@pytest.mark.parametrize(
    "name", ["mithril.LICENSE", "../app.js", "vendor/mithril.js", "", "/etc/passwd"]
)
def test_vendor_asset_rejects_other_names(name: str) -> None:
    with pytest.raises(ValueError, match="unknown vendor asset"):
        vendor_asset(name)


def test_token_css_has_known_token() -> None:
    assert "--vd-ink" in token_css()
