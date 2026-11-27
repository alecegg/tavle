"""Fail when a test removed since BASE is missing from the area's audit file.

Usage: scripts/check_audit_removals.py BASE AREA

Compares each test file that `git diff --name-only BASE` lists with its content at BASE.
A Python test is `def test_...` or `async def test_...` at any indent; a JavaScript test
is the title of an `it(` or `test(` call. A name counts as removed when the file at BASE
had it and the working-tree file no longer does. Each removed name must appear as a
whole word in `openspec/changes/tavle-test-audit/audit/AREA.md`, or the script exits 1.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = Path("openspec/changes/tavle-test-audit/audit")
PY_TEST = re.compile(r"^[ \t]*(?:async[ \t]+)?def[ \t]+(test_\w*)", re.MULTILINE)
JS_TEST = re.compile(r"""^[ \t]*(?:it|test)\([ \t]*(['"`])(.+?)\1""", re.MULTILINE)


def is_test_path(path: str) -> bool:
    return path.startswith("tests/") and path.endswith((".py", ".test.js"))


def test_names(path: str, text: str) -> set[str]:
    if path.endswith(".py"):
        return set(PY_TEST.findall(text))
    return {match.group(2) for match in JS_TEST.finditer(text)}


def removed_names(base: dict[str, str], working: dict[str, str]) -> list[str]:
    removed: set[str] = set()
    for path, base_text in base.items():
        removed |= test_names(path, base_text) - test_names(path, working.get(path, ""))
    return sorted(removed)


def unrecorded(names: list[str], audit_text: str) -> list[str]:
    return [
        name for name in names if not re.search(rf"\b{re.escape(name)}\b", audit_text)
    ]


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run git in the repository with the arguments this script builds."""
    git = shutil.which("git") or "git"
    # S603: BASE is a git revision the caller passes; the command is fixed to git.
    return subprocess.run(  # noqa: S603
        [git, "-C", str(ROOT), *args], capture_output=True, text=True, check=False
    )


def base_text(base: str, path: str) -> str:
    result = run_git(["show", f"{base}:{path}"])
    return result.stdout if result.returncode == 0 else ""


def changed_test_paths(base: str) -> list[str]:
    result = run_git(["diff", "--name-only", base])
    if result.returncode != 0:
        raise SystemExit(f"git diff failed: {result.stderr.strip()}")
    return [path for path in result.stdout.splitlines() if is_test_path(path)]


def working_text(path: str) -> str:
    full = ROOT / path
    return full.read_text() if full.is_file() else ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("base")
    parser.add_argument("area")
    args = parser.parse_args(argv)

    paths = changed_test_paths(args.base)
    base = {path: base_text(args.base, path) for path in paths}
    working = {path: working_text(path) for path in paths}
    names = removed_names(base, working)
    if not names:
        print("no test names removed")
        return 0

    audit = AUDIT_DIR / f"{args.area}.md"
    audit_text = (ROOT / audit).read_text() if (ROOT / audit).is_file() else ""
    missing = unrecorded(names, audit_text)
    for name in missing:
        print(f"removed but not recorded in {audit}: {name}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
