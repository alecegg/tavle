"""Every static ES module parses: a missing brace once shipped past the matrix."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

SRC = Path(__file__).parents[2] / "src/tavle"
# page scripts (varde.pages) and component enhancers (tavle), served together
SCRIPTS = sorted([*(SRC / "page/static").glob("*.js"), *(SRC / "static").glob("*.js")])


@pytest.mark.slow
@pytest.mark.parametrize("path", SCRIPTS, ids=lambda p: p.name)
def test_module_parses(path: Path) -> None:
    node = shutil.which("node")
    assert node
    result = subprocess.run(  # noqa: S603
        [node, "--check", "--input-type=module"],
        input=path.read_text("utf-8"),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
