"""Run mutmut over `src/tavle` in a throwaway copy of the repository.

Usage: scripts/mutate.py [--workers N] [--fresh] [--tag NAME] [--only PATTERN ...]

The copy lives under $TMPDIR/mutate-tavle (or mutate-tavle-<NAME> with --tag, so
runs with different tags can overlap), with its own venv (mutmut is a dev tool and
is never installed into the repo env) and an isolated HOME and XDG dirs. Nothing is
written to the repo. Re-running resumes mutmut's cached results; --fresh starts over
but keeps the venv. --only limits the mutants tested and counted to names matching a
glob that contains `*` (for example `tavle.theme.merge.*`) or to full mutant names;
every mutant is still generated, and the rest stay unchecked. With --only, mutmut
re-tests every matching mutant on each run, cached or not.

Test files are copied from the repository on each run, but mutmut re-copies a modified
existing test file from the copy's own `tests` into `mutants/`. When you iterate by
hand in the copy, sync a changed test file to both `mutants/tests` and `tests`, or
mutmut runs the stale file.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

MUTMUT_VERSION = "3.8.1"
REPO = Path(__file__).resolve().parents[1]
# Names left out of the copy at any depth: caches and tool state tests never read.
COPY_EXCLUDES = (
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".fallow",
    "mutants",
    "iso",
)
# Top-level copy entries that belong to the run, not the repository.
RUN_STATE = frozenset({".venv", "mutants", "iso"})
# Tests that cannot pass in a copy, as pytest node ids. Each entry needs its reason.
UNSUPPORTED_IN_COPY: tuple[str, ...] = (
    # Installs a wheel of the copy into a clean venv; mutated code imports mutmut.
    "tests/page/test_wheel_standalone.py::test_wheel_exports_standalone_page",
)
# Marker expressions: what mutmut runs per mutant, and what `--slow` tries on survivors.
FAST_TESTS = "not slow and not matrix_full"
# The full widget matrix is also `slow`; it is its own gate, not a mutant judge.
SLOW_TESTS = "slow and not matrix_full"
STATUS_LINE = re.compile(r"^\s*(?P<name>\S+): (?P<status>[a-z ]+?)\s*$")
FAILED_LINE = re.compile(r"^FAILED (?P<test>\S+)", re.MULTILINE)


def pytest_selection(marker: str) -> list[str]:
    """pytest arguments that select `marker` and skip tests unsupported in a copy."""
    deselects = [a for test in UNSUPPORTED_IN_COPY for a in ("--deselect", test)]
    return ["-m", marker, *deselects]


def mutmut_config(others: list[str]) -> str:
    """The [tool.mutmut] table: mutate `src/tavle`, run `tests`.

    mutmut names a mutant after its path relative to the project root, minus a leading
    `src.`, so the names match the imports.

    mutmut runs pytest inside `mutants/`, which holds only the source paths and
    `also_copy`. Tests read other repository files, so every other top-level entry is
    copied too.
    """
    rows = ", ".join(f'"{entry}"' for entry in others)
    deselects = ", ".join(f'"{arg}"' for arg in pytest_selection(FAST_TESTS))
    return (
        "\n[tool.mutmut]\n"
        'source_paths = ["src/tavle"]\n'
        'pytest_add_cli_args_test_selection = ["tests"]\n'
        f"also_copy = [{rows}]\n"
        f"pytest_add_cli_args = [{deselects}]\n"
    )


def parse_results(text: str) -> dict[str, list[str]]:
    """Group the mutant names printed by `mutmut results --all true` by status."""
    grouped: dict[str, list[str]] = {}
    for line in text.splitlines():
        found = STATUS_LINE.match(line)
        if found and "__mutmut_" in found["name"]:
            grouped.setdefault(found["status"], []).append(found["name"])
    return grouped


def matching(
    grouped: dict[str, list[str]], patterns: list[str]
) -> dict[str, list[str]]:
    """Keep the mutants whose names match a pattern; no patterns keeps all."""
    if not patterns:
        return grouped
    kept = {
        status: [n for n in names if any(fnmatch.fnmatch(n, p) for p in patterns)]
        for status, names in grouped.items()
    }
    return {status: names for status, names in kept.items() if names}


def summary(grouped: dict[str, list[str]]) -> str:
    total = sum(len(names) for names in grouped.values())
    parts = ", ".join(
        f"{status} {len(names)}" for status, names in sorted(grouped.items())
    )
    return f"mutants {total}: {parts}"


STAT_KEYS = (
    "killed",
    "survived",
    "no_tests",
    "timeout",
    "suspicious",
    "segfault",
    "skipped",
    "total",
)


def counts(grouped: dict[str, list[str]]) -> dict[str, int]:
    """Counts per stat key of the mutants this run judged.

    mutmut's `export-cicd-stats` counts every generated mutant, so with `--only` its
    total includes mutants the run never tested. The matched results do not.
    """
    found = {key: len(grouped.get(key.replace("_", " "), [])) for key in STAT_KEYS}
    found["total"] = sum(len(names) for names in grouped.values())
    return found


def score(stats: dict[str, int]) -> int:
    denominator = stats["total"] - stats["skipped"]
    return 100 * stats["killed"] // denominator if denominator > 0 else 0


def passes_floor(stats: dict[str, int], floor: int) -> bool:
    return stats["skipped"] == 0 and score(stats) >= floor


def effective_floor(floor: int, minimum: int) -> int:
    return max(floor, minimum)


def failed_tests(output: str) -> list[str]:
    """Names of the tests that failed in mutmut's clean run, in output order."""
    return FAILED_LINE.findall(output)


def top_level_entries() -> list[Path]:
    """Every repository entry outside `src` that tests may read, directories first.

    Directories come first because mutmut copies files only into existing directories.
    """
    skipped = {*COPY_EXCLUDES, "src"}
    kept = [p for p in REPO.iterdir() if p.name not in skipped]
    return sorted(kept, key=lambda p: (not p.is_dir(), p.name))


def tools_dir(tool: str) -> str:
    found = shutil.which(tool)
    return str(Path(found).parent) if found else "/usr/bin"


def work_dir(tag: str) -> Path:
    suffix = f"-{tag}" if tag else ""
    return Path(tempfile.gettempdir()) / f"mutate-tavle{suffix}"


def isolated_env(work: Path) -> dict[str, str]:
    """A minimal environment that cannot reach the user's live stores."""
    iso = work / "iso"
    for name in ("home", "xdg"):
        (iso / name).mkdir(parents=True, exist_ok=True)
    return {
        "PATH": f"{work / '.venv' / 'bin'}:{tools_dir('uv')}:/usr/bin:/bin",
        "HOME": str(iso / "home"),
        "TMPDIR": tempfile.gettempdir(),
        "XDG_DATA_HOME": str(iso / "xdg"),
        "XDG_CONFIG_HOME": str(iso / "home" / ".config"),
        "UV_CACHE_DIR": os.environ.get(
            "UV_CACHE_DIR", str(Path.home() / ".cache" / "uv")
        ),
        "UV_OFFLINE": "1",
        # Browser binaries only; slow tests need them and the copy's HOME is empty.
        "PLAYWRIGHT_BROWSERS_PATH": os.environ.get(
            "PLAYWRIGHT_BROWSERS_PATH", str(Path.home() / ".cache" / "ms-playwright")
        ),
    }


def execute(
    command: list[str], cwd: Path, env: dict[str, str], *, check: bool
) -> subprocess.CompletedProcess[str]:
    """Run a fixed tool command (uv, mutmut, pkill) in the copy; the only spawn here."""
    return subprocess.run(  # noqa: S603
        command, cwd=cwd, env=env, capture_output=True, text=True, check=check
    )


def remove_entry(entry: Path) -> None:
    if entry.is_dir() and not entry.is_symlink():
        shutil.rmtree(entry)
        return
    entry.unlink()


def discard_copy(work: Path) -> None:
    """Remove the copy but keep its venv, which costs a minute to rebuild."""
    for entry in work.iterdir() if work.is_dir() else ():
        if entry.name != ".venv":
            remove_entry(entry)


def copy_repo(work: Path) -> None:
    """Refresh the copy with mtimes kept; mutmut rewrites `mutants/` from it.

    `mutants/` and the isolated dirs are run state and survive the refresh, so a
    resumed run finds mutmut's cached results.
    """
    work.mkdir(parents=True, exist_ok=True)
    for entry in work.iterdir():
        if entry.name not in RUN_STATE:
            remove_entry(entry)
    ignore = shutil.ignore_patterns(*COPY_EXCLUDES)
    for entry in [REPO / "src", *top_level_entries()]:
        target = work / entry.name
        if entry.is_dir():
            shutil.copytree(entry, target, symlinks=True, ignore=ignore)
            continue
        shutil.copy2(entry, target, follow_symlinks=False)


def prepare_venv(work: Path) -> None:
    """Sync the locked dev env offline, then pin mutmut (the one network fetch)."""
    if (work / ".venv" / "bin" / "mutmut").exists():
        return
    env = {key: value for key, value in os.environ.items() if key != "VIRTUAL_ENV"}
    execute(["uv", "sync", "--offline", "--locked"], work, env, check=True)
    pin = f"mutmut=={MUTMUT_VERSION}"
    execute(["uv", "pip", "install", pin], work, env, check=True)


def mutmut(
    work: Path, env: dict[str, str], *args: str
) -> subprocess.CompletedProcess[str]:
    command = [str(work / ".venv" / "bin" / "mutmut"), *args]
    return execute(command, work, env, check=False)


def stop_copy_processes(work: Path) -> None:
    """Kill every process started from the copy: tests can leave a detached daemon."""
    pattern = f"(^| ){re.escape(str(work))}/"
    done = execute(["pkill", "-f", pattern], REPO, dict(os.environ), check=False)
    if done.returncode not in (0, 1):
        print(f"mutate: pkill failed ({done.stderr.strip()}); check {work} for daemons")


def mutate_in_copy(
    workers: int, work: Path, patterns: list[str]
) -> subprocess.CompletedProcess[str]:
    """Refresh the copy, append the mutmut config, and run mutmut over it."""
    copy_repo(work)
    prepare_venv(work)
    others = [entry.name for entry in top_level_entries()]
    with (work / "pyproject.toml").open("a", encoding="utf-8") as config:
        config.write(mutmut_config(others))
    stale_stats = work / "mutants" / "mutmut-stats.json"  # stale test mapping
    stale_stats.unlink(missing_ok=True)
    env = isolated_env(work)
    return mutmut(work, env, "run", "--max-children", str(workers), "--", *patterns)


def report_clean_run_failure(failing: list[str]) -> int:
    print("mutate: clean run failed in the copy; failing tests:", file=sys.stderr)
    print("\n".join(failing), file=sys.stderr)
    return 1


def report_mutmut_failure(output: str) -> None:
    tail = output.splitlines()[-10:]
    print("mutate: mutmut failed:\n" + "\n".join(tail), file=sys.stderr)


def run(work: Path, workers: int, patterns: list[str], minimum: int) -> int:
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    try:
        done = mutate_in_copy(workers, work, patterns)
    finally:
        stop_copy_processes(work)
    output = done.stdout + done.stderr
    (work / "run.log").write_text(output, encoding="utf-8")
    failing = failed_tests(output)
    if failing:
        return report_clean_run_failure(failing)
    if done.returncode != 0:
        report_mutmut_failure(output)
    results = mutmut(work, isolated_env(work), "results", "--all", "true")
    grouped = matching(parse_results(results.stdout), patterns)
    if patterns and not grouped:
        print(f"mutate: no mutant matches --only {' '.join(patterns)}", file=sys.stderr)
        return 2
    survivors = work / "survivors.txt"
    survivors.write_text(
        "\n".join(grouped.get("survived", [])) + "\n", encoding="utf-8"
    )
    print(f"mutate tavle: {summary(grouped)}")
    print(f"survivors: {survivors} (details: mutmut show <name> in {work})")
    stats = counts(grouped)
    floor = json.loads(
        (REPO / "scripts" / "mutation-floors.json").read_text(encoding="utf-8")
    )["python"]
    print(", ".join(f"{key} {stats[key]}" for key in STAT_KEYS))
    print(f"score {score(stats)}% (floor {effective_floor(floor, minimum)}%)")
    return int(
        done.returncode != 0 or not passes_floor(stats, effective_floor(floor, minimum))
    )


def slow_killer(work: Path, name: str) -> str:
    """The first slow test that fails with mutant `name` active, or `survived`."""
    command = [str(work / ".venv" / "bin" / "pytest"), "-x", "-q", "-n", "3"]
    command += ["-p", "no:cacheprovider", *pytest_selection(SLOW_TESTS), "tests"]
    env = isolated_env(work) | {"MUTANT_UNDER_TEST": name}
    result = execute(command, work / "mutants", env, check=False)
    failures = failed_tests(result.stdout + result.stderr)
    return failures[0] if failures else "survived"


def run_slow(work: Path, patterns: list[str]) -> int:
    """Try each survivor of the last fast run in this copy against the slow tests."""
    survivors = work / "survivors.txt"
    if not survivors.exists():
        print(f"mutate: no {survivors}; run without --slow first", file=sys.stderr)
        return 2
    names = survivors.read_text(encoding="utf-8").split()
    names = matching({"survived": names}, patterns).get("survived", [])
    killers = {name: slow_killer(work, name) for name in names}
    for name, killer in killers.items():
        print(f"{name}: {killer}")
    killed = sum(killer != "survived" for killer in killers.values())
    print(f"mutate tavle --slow: slow-only {killed}, survived {len(names) - killed}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument(
        "--slow",
        action="store_true",
        help="try the last run's survivors against the slow tests; print each killer",
    )
    parser.add_argument(
        "--tag", default="", help="separate copy name, lets two runs overlap"
    )
    parser.add_argument(
        "--fresh", action="store_true", help="discard the cached copy and results"
    )
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="PATTERN",
        help="test and count only mutants whose names match this glob (repeatable)",
    )
    parser.add_argument("--clean", action="store_true", help="delete the copy and exit")
    parser.add_argument("--min-score", type=int, default=0)
    args = parser.parse_args()
    if args.tag and not re.fullmatch(r"[A-Za-z0-9_-]+", args.tag):
        parser.error("tag must contain only letters, digits, underscores or hyphens")
    work = work_dir(args.tag)
    if args.clean:
        if work.exists():
            shutil.rmtree(work)
        return 0
    if args.fresh:
        discard_copy(work)
    if args.slow:
        return run_slow(work, args.only)
    return run(work, args.workers, args.only, args.min_score)


if __name__ == "__main__":
    raise SystemExit(main())
