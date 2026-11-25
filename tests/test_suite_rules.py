"""Standing rules for browser tests and disabled tests."""

import ast
import re
from pathlib import Path

TESTS = Path(__file__).parent


def unmarked_browser_files(paths: list[Path]) -> list[Path]:
    violations = []
    for path in paths:
        tree = ast.parse(path.read_text())
        imports_browser = any(
            isinstance(node, ast.Import)
            and any(a.name.split(".")[0] == "playwright" for a in node.names)
            or isinstance(node, ast.ImportFrom)
            and (node.module or "").split(".")[0] == "playwright"
            for node in ast.walk(tree)
        )
        marked = any(
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "pytestmark"
                for target in node.targets
            )
            and any(
                isinstance(part, ast.Attribute) and part.attr == "slow"
                for part in ast.walk(node.value)
            )
            for node in tree.body
        )
        if imports_browser and not marked:
            violations.append(path)
    return violations


def disabled_tests(paths: list[Path]) -> list[Path]:
    violations = []
    for path in paths:
        if {"node_modules", "fixtures"} & set(path.parts):
            continue
        if path.suffix == ".py":
            tree = ast.parse(path.read_text())
            if any(
                isinstance(node, ast.Attribute)
                and node.attr in {"skip", "skipif", "xfail"}
                for node in ast.walk(tree)
            ):
                violations.append(path)
        elif re.search(r"\.skip\s*\(|\bit\.todo\b|\bxit\s*\(", path.read_text()):
            violations.append(path)
    return violations


def test_unmarked_browser_rule(tmp_path: Path) -> None:
    path = tmp_path / "test_browser.py"
    path.write_text("from playwright.sync_api import sync_playwright\n")
    assert unmarked_browser_files([path]) == [path]
    path.write_text("import playwright\nimport pytest\npytestmark = pytest.mark.slow\n")
    assert unmarked_browser_files([path]) == []


def test_disabled_rule(tmp_path: Path) -> None:
    py = tmp_path / "test_bad.py"
    js = tmp_path / "bad.test.js"
    py.write_text('import pytest\npytest.skip("reason")\n')
    js.write_text('it.skip("reason", () => {})\n')
    assert disabled_tests([py, js]) == [py, js]


def test_real_browser_files_are_marked() -> None:
    files = list(TESTS.rglob("test_*.py"))
    assert files
    assert not unmarked_browser_files(files)


def test_real_tests_are_enabled() -> None:
    files = [*TESTS.rglob("*.py"), *TESTS.rglob("*.test.js")]
    assert any(path.suffix == ".js" for path in files)
    assert not disabled_tests(files)
