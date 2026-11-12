"""Browser side of the matrix: browsers, served pages, tab walks, shots."""

from __future__ import annotations

import os
import shutil
import tempfile
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from varde_pages.serve import PageServer

from . import audit, checks
from .cells import FIXTURES, WALK_MODES, Cell, families_in, scope_for
from .rendered import ROOTS_JS, NotRendered, not_rendered

TAB_LIMIT = 150
VIEWPORT_HEIGHT = 800
ZOOM_FACTOR = 2
SHOTS_ENV = "VARDE_WIDGET_SHOTS"  # set it to also save full-page PNGs


def shots_dir() -> Path | None:
    """Where full-page PNGs go: only when `$VARDE_WIDGET_SHOTS` is set."""
    kept = os.environ.get(SHOTS_ENV)
    if not kept:
        return None
    path = Path(kept)
    path.mkdir(parents=True, exist_ok=True)
    return path


def context_options(mode: str) -> dict[str, Any]:
    """Options only a context can set; width, scheme and media are set per load."""
    extra: dict[str, dict[str, Any]] = {
        "coarse": {"has_touch": True, "is_mobile": True},
        "nojs": {"java_script_enabled": False},
    }
    return extra.get(mode, {})


def prepare_page(context: Any, page: Any, cell: Cell) -> None:
    """Width, scheme and emulation for one load on a page reused across loads."""
    page.set_viewport_size({"width": cell.width, "height": VIEWPORT_HEIGHT})
    page.emulate_media(**media_options(cell))
    if cell.mode == "zoom200":
        cdp = context.new_cdp_session(page)
        cdp.send(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": cell.width,
                "height": VIEWPORT_HEIGHT,
                "deviceScaleFactor": ZOOM_FACTOR,
                "mobile": False,
            },
        )


def media_options(cell: Cell) -> dict[str, str]:
    options = {"color_scheme": cell.scheme}
    extra = {
        "reduced-motion": {"reduced_motion": "reduce"},
        "forced-colors": {"forced_colors": "active"},
        "print": {"media": "print"},
    }
    return options | extra.get(cell.mode, {})


def tab_walk(page: Any, scope: dict[str, Any]) -> list[dict[str, Any]]:
    """Focus the first control in `scope`, then Tab until focus leaves it."""
    page.keyboard.press("Shift")  # keyboard modality, so :focus-visible applies
    if not page.evaluate(audit.FIRST_FOCUS_JS, scope):
        return []
    stops: list[dict[str, Any]] = []
    for _ in range(TAB_LIMIT):
        stop = page.evaluate(audit.FOCUS_JS, scope)
        if stop is None:
            break
        stops.append(stop)
        page.keyboard.press("Tab")
    return stops


def audit_family(page: Any, cell: Cell, family: str) -> list[str]:
    scope = scope_for(family)
    snapshot = page.evaluate(audit.COLLECT_JS, scope)
    stops = tab_walk(page, scope) if cell.mode in WALK_MODES else []
    return checks.run_checks(
        snapshot, stops, scheme=cell.scheme, mode=cell.mode, family=family
    )


@dataclass
class Tab:
    browser: Any
    context: Any
    page: Any


class Matrix:
    """Serves the fixtures once and audits each page load for all its families."""

    def __init__(self, launch: Callable[[], Any]) -> None:
        self.launch = launch
        self.root = Path(tempfile.mkdtemp(prefix="widget-matrix-"))
        self.shots = shots_dir()
        self.tabs: dict[str, Tab] = {}
        self.servers: dict[str, tuple[PageServer, threading.Thread]] = {}
        self.failures: dict[tuple[str, int, str, str], NotRendered] = {}
        self.results: dict[tuple[str, int, str, str], dict[str, list[str]]] = {}
        shutil.copytree(FIXTURES, self.root, dirs_exist_ok=True)

    def url(self, fixture: str) -> str:
        if fixture not in self.servers:
            server = PageServer(self.root / fixture, 0, allow_edit=True)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.servers[fixture] = (server, thread)
        return f"http://127.0.0.1:{self.servers[fixture][0].port}/"

    def text(self, fixture: str) -> str:
        return (self.root / fixture).read_text(encoding="utf-8")

    def shot_path(self, cell: Cell) -> Path | None:
        if self.shots is None:
            return None
        stem = cell.fixture.removesuffix(".md")
        return self.shots / f"{stem}-{cell.mode}-{cell.scheme}-w{cell.width}.png"

    def problems(self, cell: Cell) -> list[str]:
        if cell.page_key in self.failures:
            raise self.failures[cell.page_key]
        if cell.page_key not in self.results:
            try:
                self.results[cell.page_key] = self._load(cell)
            except NotRendered as error:
                self.failures[cell.page_key] = error
                raise
        return self.results[cell.page_key][cell.family]

    def _tab(self, mode: str) -> Tab:
        """One browser and page per mode, reused: single-process dies on close."""
        if mode not in self.tabs:
            browser = self.launch()
            context = browser.new_context(**context_options(mode))
            page = context.new_page()
            page.set_default_timeout(15_000)
            self.tabs[mode] = Tab(browser, context, page)
        return self.tabs[mode]

    def _discard(self, mode: str) -> None:
        tab = self.tabs.pop(mode, None)
        if tab is not None:
            tab.browser.close()

    def _load(self, cell: Cell) -> dict[str, list[str]]:
        tab = self._tab(cell.mode)
        try:
            return self._audit(tab, cell)
        except NotRendered:
            raise
        except BaseException:
            self._discard(cell.mode)  # a hung or crashed page must not leak forward
            raise

    def _audit(self, tab: Tab, cell: Cell) -> dict[str, list[str]]:
        prepare_page(tab.context, tab.page, cell)
        tab.page.goto(self.url(cell.fixture))
        if cell.mode == "rtl":
            tab.page.evaluate("document.documentElement.dir = 'rtl'")
        shot = self.shot_path(cell)
        if shot is not None:
            tab.page.screenshot(path=str(shot), full_page=True)
        missing = not_rendered(
            self.text(cell.fixture),
            tab.page.evaluate(ROOTS_JS),
            nojs=cell.mode == "nojs",
        )
        if missing:
            raise NotRendered(f"{cell.fixture} is not rendered: " + "; ".join(missing))
        return {f: audit_family(tab.page, cell, f) for f in families_in(cell.fixture)}

    def close(self) -> None:
        for server, thread in self.servers.values():
            server.shutdown()
            server.server_close()
            thread.join(5)
        for mode in list(self.tabs):
            self._discard(mode)
        shutil.rmtree(self.root, ignore_errors=True)
