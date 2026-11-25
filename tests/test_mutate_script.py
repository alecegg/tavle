import importlib.util
import sys
from pathlib import Path


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
