"""Standalone command smoke tests."""

import asyncio
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from browser_args import BROWSER_ARGS
from playwright.sync_api import sync_playwright

from tavle import PageServer


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


def test_commands(tmp_path: Path) -> None:
    doc = tmp_path / "page.md"
    doc.write_text("# Title\n\n```ui\nx = unknown\n```\n")
    result = command("check", doc, "--json")
    assert result.returncode == 1
    assert json.loads(result.stdout)["errors"][0]["line"] == 4
    assert f"{doc}:4:" in command("check", doc).stdout
    assert command("render", doc).stdout.startswith('<main data-role="page">')
    output = tmp_path / "out.html"
    assert command("export", doc, "--out", output).returncode == 0
    html = output.read_text()
    assert "<script src" not in html and "<link href" not in html
    doc.with_name(doc.name + ".comments.jsonl").write_text(
        '{"id":"c1","state":"open","text":"Hello"}\n'
    )
    assert "Hello" in command("comments", doc).stdout
    assert command("render", tmp_path / "missing").returncode == 2


def test_export_refuses_to_overwrite_its_source(tmp_path: Path) -> None:
    doc = tmp_path / "page.md"
    doc.write_text("# Title\n")
    result = command("export", doc, "--out", doc)
    assert result.returncode == 1
    assert "would overwrite the source" in result.stderr
    assert doc.read_text() == "# Title\n"


def test_theme_flag(tmp_path: Path) -> None:
    doc = tmp_path / "page.md"
    doc.write_text("# Page\n")
    theme = tmp_path / "theme.toml"
    theme.write_text('preset = "paper"\n')
    plain = command("render", doc)
    themed = command("render", doc, "--theme", theme)
    assert themed.returncode == 0
    assert "data-vd-theme" in themed.stdout
    assert themed.stdout != plain.stdout


def test_check_warnings_and_task_ids(tmp_path: Path) -> None:
    doc = tmp_path / "page.md"
    doc.write_text(
        "# Title\n\n```ui\n"
        't = table(columns: ["a"], rows: [["1"]], covers: ["task-a"])\n```\n'
    )
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    (tasks / "task-a.md").write_text("# Task\n")
    result = command("check", doc, "--json")
    findings = json.loads(result.stdout)
    assert result.returncode == 0
    assert findings["warnings"]
    assert not any("task-a" in str(w) for w in findings["warnings"])
    doc.write_text("# Title\n\n```ui\nx = unknown\n```\n")
    assert command("check", doc).returncode == 1


def test_theme_ignores_other_config(tmp_path: Path) -> None:
    doc = tmp_path / "page.md"
    doc.write_text("# Page\n")
    theme = tmp_path / "theme.toml"
    theme.write_text('preset = "paper"\n')
    expected = command("render", doc, "--theme", theme)
    config = tmp_path / "config"
    config.mkdir()
    (config / "theme.toml").write_text('preset = "harbor"\n')
    env = {**os.environ, "HOME": str(config), "XDG_CONFIG_HOME": str(config)}
    actual = command("render", doc, "--theme", theme, env=env)
    assert actual.returncode == 0
    assert actual.stdout == expected.stdout
    assert actual.stdout != command("render", doc, env=env).stdout


@pytest.mark.slow
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
