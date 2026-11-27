import importlib.util
from pathlib import Path

import pytest


def load_script():
    path = Path(__file__).resolve().parents[1] / "scripts" / "mutation_gate.py"
    spec = importlib.util.spec_from_file_location("mutation_gate", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def report_with(*statuses: str) -> dict:
    mutants = [{"status": status} for status in statuses]
    return {
        "schemaVersion": "1",
        "files": {"src/tavle/static/a.js": {"mutants": mutants}},
    }


def test_lower_working_floor_fails():
    module = load_script()
    problems = module.floor_problems({"python": 40, "js": 10}, {"python": 50, "js": 10})
    assert problems == ["python: working floor 40 is below base floor 50"]


def test_equal_or_higher_floors_pass():
    module = load_script()
    assert (
        module.floor_problems({"python": 50, "js": 10}, {"python": 50, "js": 10}) == []
    )
    assert (
        module.floor_problems({"python": 60, "js": 20}, {"python": 50, "js": 10}) == []
    )


def test_missing_floor_key_fails():
    module = load_script()
    assert module.floor_problems({"python": 50}, {"python": 50, "js": 10}) == [
        "js: floor missing from the floors file"
    ]
    assert module.floor_problems({"python": 50, "js": 10}, {"python": 50}) == [
        "js: floor missing from the floors file"
    ]


def test_floor_of_zero_fails_only_for_a_language_the_change_mutates():
    module = load_script()
    floors = {"python": 0, "js": 0}
    assert module.unset_floors(floors, ["python"]) == [
        "python: floor 0 is below 1; set it from a measured run"
    ]
    assert module.unset_floors(floors, []) == []


def test_js_timeout_never_counts_as_killed():
    module = load_script()
    assert module.js_percent({"Killed": 1, "Timeout": 1}) == 50
    assert module.js_percent({"Killed": 1}) == 100


def test_survivor_turning_into_timeout_does_not_raise_the_js_score():
    module = load_script()
    before = module.js_percent({"Killed": 5, "Survived": 5})
    after = module.js_percent({"Killed": 5, "Survived": 4, "Timeout": 1})
    assert before == after == 50


def test_js_denominator_counts_no_coverage_and_runtime_errors_only():
    module = load_script()
    counts = {
        "Killed": 2,
        "NoCoverage": 1,
        "RuntimeError": 1,
        "CompileError": 9,
        "Ignored": 9,
    }
    assert module.js_percent(counts) == 50


def test_js_score_without_mutants_is_zero():
    module = load_script()
    assert module.js_percent({}) == 0


def test_js_status_counts_reads_every_file():
    module = load_script()
    report = {
        "files": {
            "src/tavle/static/a.js": {"mutants": [{"status": "Killed"}]},
            "src/tavle/static/b.js": {
                "mutants": [{"status": "Timeout"}, {"status": "Killed"}]
            },
        }
    }
    assert module.js_status_counts(report) == {"Killed": 2, "Timeout": 1}


def test_js_run_at_the_floor_passes_and_below_fails():
    module = load_script()
    report = report_with("Killed", "Killed", "Survived", "Survived")
    assert module.js_problems(0, "", ["a.js"], report, 50) == []
    assert module.js_problems(0, "", ["a.js"], report, 51) == [
        "js: score 50% is below the floor 51%"
    ]


def test_timeout_in_a_run_scores_as_not_killed():
    module = load_script()
    report = report_with("Killed", "Timeout")
    assert module.js_problems(0, "", ["a.js"], report, 51) == [
        "js: score 50% is below the floor 51%"
    ]


def test_no_tests_line_fails_and_names_the_changed_files():
    module = load_script()
    output = "Error: No tests were executed. Stryker will exit prematurely."
    problems = module.js_problems(
        1, output, ["src/tavle/static/a.js", "src/tavle/static/b.js"], None, 1
    )
    assert problems == [
        (
            "js: no tests relate to src/tavle/static/a.js, src/tavle/static/b.js; "
            "their mutants score as NoCoverage"
        )
    ]


def test_js_run_without_a_fresh_report_fails():
    module = load_script()
    assert module.js_problems(0, "", ["a.js"], None, 1) == [
        "js: no mutation report written by this run"
    ]


def test_js_nonzero_exit_fails_even_with_a_report():
    module = load_script()
    report = report_with("Killed")
    assert module.js_problems(2, "", ["a.js"], report, 1) == ["js: mutate-js exited 2"]


def test_python_run_fails_on_nonzero_exit_only():
    module = load_script()
    assert module.python_problems(0) == []
    assert module.python_problems(1) == ["python: mutate.py exited 1"]


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("src/tavle/static/dom.js", True),
        ("src/tavle/static/vendor/mithril.js", False),
        ("src/tavle/static/dom.css", False),
        ("tests/test_x.test.js", False),
    ],
)
def test_changed_js_selects_static_modules_outside_vendor(path, expected):
    module = load_script()
    assert (path in module.changed_js([path])) is expected


def test_changed_python_selects_package_modules():
    module = load_script()
    paths = ["src/tavle/cli.py", "scripts/mutate.py", "tests/test_cli.py"]
    assert module.changed_python(paths) == ["src/tavle/cli.py"]


def test_scoped_languages_for_all_modules_is_every_language():
    module = load_script()
    assert module.scoped_languages(None, []) == ["python", "js"]


def test_scoped_languages_follows_changed_paths():
    module = load_script()
    assert module.scoped_languages("HEAD", ["src/tavle/static/dom.js"]) == ["js"]
    assert module.scoped_languages("HEAD", ["README.md"]) == []


def test_main_needs_exactly_one_of_base_or_all():
    module = load_script()
    with pytest.raises(SystemExit):
        module.main([])
    with pytest.raises(SystemExit):
        module.main(["HEAD", "--all"])
