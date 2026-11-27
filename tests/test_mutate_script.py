import importlib.util
import sys
import sysconfig
import venv
from pathlib import Path

import pytest


def load_script():
    path = Path(__file__).resolve().parents[1] / "scripts" / "mutate.py"
    spec = importlib.util.spec_from_file_location("mutate_script", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_config_selects_fast_tests():
    config = load_script().mutmut_config([])
    assert '"-m", "not slow and not matrix_full"' in config


def test_default_workers(monkeypatch):
    module = load_script()
    monkeypatch.setattr(sys, "argv", ["mutate.py"])
    monkeypatch.setattr(module, "run", lambda work, workers, patterns, minimum: workers)
    assert module.main() == 2


def test_slow_selection_skips_tests_unsupported_in_a_copy():
    module = load_script()
    selection = module.pytest_selection(module.SLOW_TESTS)
    assert selection[:2] == ["-m", "slow and not matrix_full"]
    for test in module.UNSUPPORTED_IN_COPY:
        assert ["--deselect", test] == selection[selection.index(test) - 1 :][:2]


def test_slow_needs_a_previous_run(tmp_path, capsys):
    assert load_script().run_slow(tmp_path, []) == 2
    assert "run without --slow first" in capsys.readouterr().err


def test_slow_prints_each_survivors_killer(tmp_path, monkeypatch, capsys):
    module = load_script()
    names = ["tavle.a.x__mutmut_1", "tavle.a.x__mutmut_2", "tavle.b.y__mutmut_1"]
    (tmp_path / "survivors.txt").write_text("\n".join(names) + "\n")
    killers = {names[0]: "tests/page/test_a.py::test_a", names[1]: "survived"}
    monkeypatch.setattr(module, "slow_killer", lambda work, name: killers[name])
    assert module.run_slow(tmp_path, ["tavle.a.*"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out == [
        "tavle.a.x__mutmut_1: tests/page/test_a.py::test_a",
        "tavle.a.x__mutmut_2: survived",
        "mutate tavle --slow: slow-only 1, survived 1",
    ]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


# Each mutant name triggers one way a slow run can end.
MUTATED_PROBE = """\
import os
import time

MUTANT = os.environ.get("MUTANT_UNDER_TEST")
if MUTANT == "import-error":
    raise ImportError(MUTANT)


def answer():
    if MUTANT == "crash":
        os._exit(3)
    if MUTANT == "hang":
        time.sleep(30)
    return 2 if MUTANT == "mutant" else 1
"""


def fixture_copy(work: Path) -> None:
    """A work copy whose venv installs `src` editably; `mutants/src` holds a mutant."""
    venv.create(work / ".venv", symlinks=True)
    python = work / ".venv" / "bin" / "python"
    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    site = work / ".venv" / "lib" / version / "site-packages"
    write(site / "editable.pth", f"{work / 'src'}\n{sysconfig.get_path('purelib')}\n")
    runner = work / ".venv" / "bin" / "pytest"
    write(
        runner, f"#!{python}\nimport pytest\nraise SystemExit(pytest.console_main())\n"
    )
    runner.chmod(0o755)
    write(work / "src" / "probe.py", "def answer():\n    return 1\n")
    write(work / "mutants" / "src" / "probe.py", MUTATED_PROBE)
    write(
        work / "mutants" / "pytest.ini",
        "[pytest]\nmarkers = slow\ntimeout = 2\ntimeout_method = thread\n",
    )
    write(
        work / "mutants" / "tests" / "test_probe.py",
        "import probe\nimport pytest\n\n\n@pytest.mark.slow\n"
        "def test_answer():\n    assert probe.answer() == 1\n",
    )


@pytest.mark.slow
def test_slow_killer_runs_the_mutated_tree(tmp_path):
    fixture_copy(tmp_path)
    slow_killer = load_script().slow_killer
    assert slow_killer(tmp_path, "mutant") == "tests/test_probe.py::test_answer"
    assert slow_killer(tmp_path, "other") == "survived"


@pytest.fixture(scope="module")
def probe_copy(tmp_path_factory):
    work = tmp_path_factory.mktemp("probe")
    fixture_copy(work)
    return work


CRASHED = "worker crashed or timed out in tests/test_probe.py::test_answer"


@pytest.mark.slow
@pytest.mark.parametrize(
    ("mutant", "reason"),
    [
        ("import-error", "pytest exit 2: tests/test_probe.py"),
        ("crash", CRASHED),
        ("hang", CRASHED),
    ],
)
def test_slow_killer_reports_a_broken_run_as_error(probe_copy, mutant, reason):
    assert load_script().slow_killer(probe_copy, mutant) == f"error: {reason}"


def test_slow_verdict():
    verdict = load_script().slow_verdict
    crash = "worker 'gw0' crashed while running 't.py::a[x y]'\nFAILED t.py::a[x y]\n"
    cases = [
        (0, "1 passed", "survived"),
        (2, "FAILED t.py::b - assert 0\nERROR t.py::c - boom", "t.py::b"),
        (1, crash + "FAILED t.py::b - assert 0", "t.py::b"),
        (2, "ERROR t.py::c - boom", "error: pytest exit 2: t.py::c - boom"),
        (5, "no tests ran", "error: pytest exit 5"),
        (-11, "", "error: pytest exit -11"),
    ]
    for returncode, output, expected in cases:
        assert verdict(returncode, output) == expected


def test_slow_counts_errors_apart(tmp_path, monkeypatch, capsys):
    module = load_script()
    results = {"m.a__mutmut_1": "error: pytest exit 3", "m.a__mutmut_2": "survived"}
    (tmp_path / "survivors.txt").write_text("\n".join(results) + "\n")
    monkeypatch.setattr(module, "slow_killer", lambda work, name: results[name])
    assert module.run_slow(tmp_path, []) == 0
    assert capsys.readouterr().out.splitlines() == [
        "m.a__mutmut_2: survived",
        "mutate tavle --slow: slow-only 0, survived 1",
        "mutate tavle --slow: error 1, neither killed nor survived",
        "m.a__mutmut_1: error: pytest exit 3",
    ]


def test_score_and_floor():
    module = load_script()
    stats = {"killed": 1, "survived": 1, "timeout": 0, "skipped": 0, "total": 2}
    assert module.score(stats) == 50
    assert module.passes_floor(stats, 50)
    assert not module.passes_floor(stats, 51)
    assert module.score(stats | {"survived": 0, "timeout": 1}) == 50
    assert not module.passes_floor(stats | {"skipped": 1}, 0)
    assert module.effective_floor(50, 0) == 50


def test_counts_judge_only_the_matched_mutants():
    module = load_script()
    grouped = {"killed": ["a", "b"], "no tests": ["c"], "not checked": ["d"]}
    stats = module.counts(grouped)
    assert (stats["killed"], stats["no_tests"], stats["total"]) == (2, 1, 4)
    assert module.score(stats) == 50


def test_changed_module_patterns():
    paths = [
        "src/tavle/a/b.py",
        "src/tavle/a/__init__.py",
        "src/tavle/a/x.css",
        "other/x.py",
    ]
    assert load_script().changed_module_patterns(paths) == [
        "tavle.a.b.*",
        "tavle.a.x_*",
        "tavle.a.xǁ*",
    ]


def test_affected_mutants():
    module = load_script()
    stats = {"f": ["tests/a.py::one", "tests/a.py::two"], "g": ["tests/b.py::one"]}
    killed = ["f__mutmut_1", "g__mutmut_1"]
    cases = [
        ({}, [], ["tests/a.py"], []),
        (stats, killed, ["tests/missing.py"], []),
        (stats, killed, ["tests/a.py::one"], ["f__mutmut_1"]),
        (stats, killed, ["tests/a.py"], ["f__mutmut_1"]),
        (stats, [], ["tests/a.py"], []),  # A timeout is absent from killed.
        (stats, killed, ["tests/a"], []),  # A path prefix is not a file.
        (stats, killed, ["tests/a.py", "tests/b.py"], ["f__mutmut_1", "g__mutmut_1"]),
    ]
    for coverage, baseline, tests, expected in cases:
        assert module.affected_mutants(coverage, baseline, tests) == expected


def test_lost_kills():
    module = load_script()
    for baseline, without, expected in [
        ([], [], []),
        (["a", "b"], ["b"], ["a"]),
        (["a"], ["a"], []),
    ]:
        assert module.lost_kills(baseline, without) == expected
