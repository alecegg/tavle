"""Exercise the installed wheel without the source tree or Varde."""

import asyncio
import base64
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

import pytest


def run(*args: str, cwd: Path, env: dict[str, str]) -> None:
    async def execute() -> None:
        process = await asyncio.create_subprocess_exec(*args, cwd=cwd, env=env)
        assert await process.wait() == 0

    asyncio.run(execute())


@pytest.mark.slow
def test_wheel_exports_standalone_page() -> None:
    project = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env["UV_OFFLINE"] = "1"
    uv = shutil.which("uv")
    assert uv is not None
    with tempfile.TemporaryDirectory(dir="/var/tmp", prefix="tavle-wheel-") as scratch:
        root = Path(scratch)
        wheels = root / "wheels"
        run(
            uv,
            "build",
            "--wheel",
            "--out-dir",
            str(wheels),
            cwd=project,
            env=env,
        )
        (wheel,) = wheels.glob("*.whl")
        venv = root / "venv"
        run(sys.executable, "-m", "venv", str(venv), cwd=root, env=env)
        python = venv / "bin" / "python"
        run(
            uv,
            "pip",
            "install",
            "--python",
            str(python),
            "--no-deps",
            str(wheel),
            cwd=root,
            env=env,
        )
        run(
            str(python),
            "-I",
            "-c",
            "import importlib.util; assert importlib.util.find_spec('varde') is None",
            cwd=root,
            env=env,
        )
        image = b'<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"></svg>'
        (root / "image.svg").write_bytes(image)
        (root / "page.md").write_text(
            '# Page\n\n```ui\nn = callout(tone: "info", text: "Hello")\n'
            'i = image(src: "image.svg", alt: "Image")\n```\n',
            encoding="utf-8",
        )
        output = root / "out.html"
        run(
            str(venv / "bin" / "tavle"),
            "export",
            "page.md",
            "--out",
            str(output),
            cwd=root,
            env=env,
        )
        html = output.read_text(encoding="utf-8")
        assert 'data-mithril="callout"' in html
        assert f"data:image/svg+xml;base64,{base64.b64encode(image).decode()}" in html
        assert not re.search(
            r"<(?:script\b[^>]*\bsrc|link\b[^>]*\bhref)\s*=", html, re.IGNORECASE
        )
    assert not root.exists()
