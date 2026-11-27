"""Gate a change on the mutation floors (design D8).

Usage: scripts/mutation_gate.py BASE | --all

Reads the working floors in scripts/mutation-floors.json and the floors at BASE (HEAD
with --all) and fails when a working floor is lower, or a key is missing. For each
language the change touches, it then fails when the floor is below 1. Changed Python
modules are mutated by `scripts/mutate.py --changed BASE` (all with --all), and changed
static JavaScript files by `just mutate-js --mutate ...` (all with --all). The
JavaScript score is computed here from the Stryker json report. Prints
`no changed modules` and exits 0 when neither language changed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
FLOOR_FILE = "scripts/mutation-floors.json"
LANGUAGES = ("python", "js")
PYTHON_PREFIX = "src/tavle/"
JS_PREFIX = "src/tavle/static/"
JS_VENDOR_PREFIX = "src/tavle/static/vendor/"
JS_REPORT = (
    REPO
    / json.loads((REPO / "stryker.config.json").read_text(encoding="utf-8"))[
        "jsonReporter"
    ]["fileName"]
)
# Stryker statuses in the denominator; Timeout counts as not killed.
JS_COUNTED = ("Killed", "Survived", "NoCoverage", "Timeout", "RuntimeError")
NO_TESTS_LINE = "No tests were executed"


def percent(part: int, whole: int) -> int:
    return 100 * part // whole if whole > 0 else 0


def floor_problems(working: Mapping[str, int], base: Mapping[str, int]) -> list[str]:
    """Missing keys and working floors lower than the base floors."""
    problems = []
    for lang in LANGUAGES:
        if lang not in working or lang not in base:
            problems.append(f"{lang}: floor missing from the floors file")
        elif working[lang] < base[lang]:
            problems.append(
                f"{lang}: working floor {working[lang]} is below base floor "
                f"{base[lang]}"
            )
    return problems


def unset_floors(floors: Mapping[str, int], languages: list[str]) -> list[str]:
    """Languages the change mutates whose floor is below 1 (0 gates nothing)."""
    return [
        f"{lang}: floor {floors.get(lang, 0)} is below 1; set it from a measured run"
        for lang in languages
        if floors.get(lang, 0) < 1
    ]


def js_status_counts(report: dict[str, Any]) -> Counter[str]:
    """Count each Stryker mutant status in a mutation-testing-report json."""
    return Counter(
        mutant["status"]
        for file in report.get("files", {}).values()
        for mutant in file.get("mutants", [])
    )


def js_percent(counts: Mapping[str, int]) -> int:
    """Killed over Killed + Survived + NoCoverage + Timeout + RuntimeError."""
    denominator = sum(counts.get(status, 0) for status in JS_COUNTED)
    return percent(counts.get("Killed", 0), denominator)


def no_tests_problem(output: str, files: list[str]) -> list[str]:
    """Stryker exits early when no test relates to the mutated files."""
    if NO_TESTS_LINE not in output:
        return []
    named = ", ".join(files) or "the static modules"
    return [f"js: no tests relate to {named}; their mutants score as NoCoverage"]


def js_problems(
    returncode: int,
    output: str,
    files: list[str],
    report: dict[str, Any] | None,
    floor: int,
) -> list[str]:
    """Verdict on one JavaScript run: its exit, its output and its scored report."""
    no_tests = no_tests_problem(output, files)
    if no_tests:
        return no_tests
    if returncode:
        return [f"js: mutate-js exited {returncode}"]
    if report is None:
        return ["js: no mutation report written by this run"]
    score = js_percent(js_status_counts(report))
    if score < floor:
        return [f"js: score {score}% is below the floor {floor}%"]
    return []


def python_problems(returncode: int) -> list[str]:
    """mutate.py exits non-zero for a score below the floor or a skipped mutant."""
    return [f"python: mutate.py exited {returncode}"] if returncode else []


def execute(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a fixed tool command in the repository; the only spawn here."""
    return subprocess.run(  # noqa: S603
        command, cwd=REPO, capture_output=True, text=True, check=False
    )


def git_stdout(*args: str) -> str:
    result = execute(["git", "-C", str(REPO), *args])
    if result.returncode:
        raise SystemExit(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def changed_paths(base: str) -> list[str]:
    """Paths changed since BASE, minus deleted files (nothing left to mutate)."""
    return git_stdout("diff", "--name-only", "--diff-filter=d", base).splitlines()


def changed_python(paths: list[str]) -> list[str]:
    return [p for p in paths if p.startswith(PYTHON_PREFIX) and p.endswith(".py")]


def changed_js(paths: list[str]) -> list[str]:
    return [
        p
        for p in paths
        if p.startswith(JS_PREFIX)
        and not p.startswith(JS_VENDOR_PREFIX)
        and p.endswith(".js")
    ]


def scoped_languages(base: str | None, paths: list[str]) -> list[str]:
    """Languages with changed modules; --all (no BASE) mutates both."""
    if base is None:
        return list(LANGUAGES)
    found = []
    if changed_python(paths):
        found.append("python")
    if changed_js(paths):
        found.append("js")
    return found


def read_working_floors() -> dict[str, int]:
    return json.loads((REPO / FLOOR_FILE).read_text(encoding="utf-8"))


def read_floors_at(rev: str) -> dict[str, int]:
    return json.loads(git_stdout("show", f"{rev}:{FLOOR_FILE}"))


def fresh_report(started: float) -> dict[str, Any] | None:
    """The Stryker json report, only if this run wrote it (stale scores nothing)."""
    if not JS_REPORT.is_file() or JS_REPORT.stat().st_mtime < started:
        return None
    return json.loads(JS_REPORT.read_text(encoding="utf-8"))


def run_python(base: str | None) -> int:
    command = [sys.executable, str(REPO / "scripts" / "mutate.py")]
    if base is not None:
        command += ["--changed", base]
    return subprocess.run(command, cwd=REPO, check=False).returncode  # noqa: S603


def run_js(files: list[str], floor: int) -> list[str]:
    """Run mutate-js over `files` (all static modules if empty), then judge it."""
    args = ["--mutate", ",".join(files)] if files else []
    started = time.time()
    done = execute(["just", "mutate-js", *args])
    output = done.stdout + done.stderr
    print(output)
    return js_problems(done.returncode, output, files, fresh_report(started), floor)


def report(problems: list[str]) -> int:
    for problem in problems:
        print(f"mutation gate: {problem}", file=sys.stderr)
    return 1 if problems else 0


def gate(base: str | None) -> int:
    languages = scoped_languages(base, changed_paths(base) if base else [])
    working = read_working_floors()
    problems = floor_problems(working, read_floors_at(base or "HEAD"))
    problems += unset_floors(working, languages)
    if problems:
        return report(problems)
    if not languages:
        print("no changed modules")
        return 0
    return report(run_languages(base, languages, working))


def run_languages(
    base: str | None, languages: list[str], floors: Mapping[str, int]
) -> list[str]:
    problems = []
    if "python" in languages:
        problems += python_problems(run_python(base))
    if "js" in languages:
        files = changed_js(changed_paths(base)) if base else []
        problems += run_js(files, floors["js"])
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "base", nargs="?", help="git revision the change is gated against"
    )
    parser.add_argument(
        "--all", action="store_true", help="mutate every module, not just changed ones"
    )
    args = parser.parse_args(argv)
    if bool(args.base) == args.all:
        parser.error("give BASE or --all")
    return gate(None if args.all else args.base)


if __name__ == "__main__":
    raise SystemExit(main())
