"""Fixtures for the widget matrix: a launcher for single-process Chromium."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

import pytest

from varde.base.browser_args import BROWSER_ARGS

from .driver import Matrix


@pytest.fixture(scope="module")
def matrix_launch() -> Iterator[Callable[[], Any]]:
    """Launch a browser; the caller closes it (single-process dies with its page)."""
    # Module scope: a live sync Playwright blocks any other in the same worker
    # (the design probe starts its own), so it must not outlive the module.
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright

        playwright = sync_playwright().start()
    except (ImportError, OSError) as exc:
        pytest.fail(f"Widget matrix needs Playwright: {exc}", pytrace=False)

    def launch() -> Any:
        try:
            return playwright.chromium.launch(args=BROWSER_ARGS)
        except (OSError, PlaywrightError) as exc:
            pytest.fail(
                f"Widget matrix could not launch Chromium: {exc}", pytrace=False
            )

    try:
        yield launch
    finally:
        playwright.stop()


@pytest.fixture(scope="module")
def matrix(matrix_launch: Callable[[], Any]) -> Iterator[Matrix]:
    holder = Matrix(matrix_launch)
    yield holder
    holder.close()
