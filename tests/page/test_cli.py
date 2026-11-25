"""Standalone command browser test."""

import asyncio
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from browser_args import BROWSER_ARGS
from playwright.sync_api import sync_playwright

from tavle import PageServer

pytestmark = pytest.mark.slow


def command(
    *args: object, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    async def invoke() -> subprocess.CompletedProcess[str]:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "tavle",
            *(str(a) for a in args),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await proc.communicate()
        return subprocess.CompletedProcess(
            [str(a) for a in args],
            proc.returncode or 0,
            stdout.decode(),
            stderr.decode(),
        )

    return asyncio.run(invoke())


def test_render_fragment_mounts(tmp_path: Path) -> None:
    doc = tmp_path / "page.md"
    doc.write_text("# Embedded\n\nHello from the fragment.\n")
    result = command("render", doc)
    assert result.returncode == 0
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=BROWSER_ARGS)
            try:
                page = browser.new_page()
                base = f"http://127.0.0.1:{server.port}"
                host = (
                    '<link rel="stylesheet" href="/static/app-inline.css">'
                    + result.stdout
                    + '<script type="module">'
                    + 'import { mountPage } from "/static/page.js";'
                    + "await mountPage(document, {readOnly: true});"
                    + "window.mounted = true;</script>"
                )
                page.route(
                    f"{base}/host",
                    lambda route: route.fulfill(body=host, content_type="text/html"),
                )
                page.goto(f"{base}/host")
                page.wait_for_function("window.mounted === true")
                main = page.locator('main[data-role="page"]')
                assert "Hello from the fragment." in main.inner_text()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)
