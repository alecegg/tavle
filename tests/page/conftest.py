"""Shared by the page library tests; copied from tests/pages/conftest.py."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _fast_server_shutdown(monkeypatch: pytest.MonkeyPatch) -> None:
    """Poll every 20 ms; the 0.5 s default delays each test teardown by up to 0.5 s."""
    from varde.pagelib.serve.serve import PageServer

    original = PageServer.serve_forever

    def serve_forever(self: PageServer, poll_interval: float = 0.02) -> None:
        original(self, poll_interval)

    monkeypatch.setattr(PageServer, "serve_forever", serve_forever)
