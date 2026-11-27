import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_audit_removals.py"


def load_script():
    spec = importlib.util.spec_from_file_location("check_audit_removals", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PY_BEFORE = """\
def test_plain():
    pass


async def test_async_case():
    pass


class TestGroup:
    def test_indented_method(self):
        pass


def helper():
    pass
"""

JS_BEFORE = """\
describe('x', () => {
  it('reports a bad input', () => {});
  test("keeps the order", () => {});
});
"""


def test_python_names_include_async_and_indented_tests():
    module = load_script()
    names = module.test_names("tests/test_x.py", PY_BEFORE)
    assert names == {"test_plain", "test_async_case", "test_indented_method"}


def test_javascript_names_are_it_and_test_titles():
    module = load_script()
    names = module.test_names("tests/components/x.test.js", JS_BEFORE)
    assert names == {"reports a bad input", "keeps the order"}


def test_removed_async_test_and_indented_method_are_listed():
    module = load_script()
    base = {"tests/test_x.py": PY_BEFORE}
    working = {"tests/test_x.py": "def test_plain():\n    pass\n"}
    assert module.removed_names(base, working) == [
        "test_async_case",
        "test_indented_method",
    ]


def test_removed_js_title_is_listed():
    module = load_script()
    base = {"tests/components/x.test.js": JS_BEFORE}
    working = {"tests/components/x.test.js": "it('reports a bad input', () => {});\n"}
    assert module.removed_names(base, working) == ["keeps the order"]


def test_removed_file_counts_every_name_as_removed():
    module = load_script()
    base = {"tests/test_x.py": "def test_gone():\n    pass\n"}
    assert module.removed_names(base, {}) == ["test_gone"]


def test_unrecorded_names_are_reported_and_recorded_ones_are_accepted():
    module = load_script()
    names = ["test_async_case", "test_indented_method", "keeps the order"]
    audit = (
        "| `test_async_case` | delete | C5 | duplicate |\n"
        "| keeps the order | delete | C5 | x |\n"
    )
    assert module.unrecorded(names, "") == names
    assert module.unrecorded(names, audit) == ["test_indented_method"]


def test_a_name_is_matched_as_a_whole_word():
    module = load_script()
    assert module.unrecorded(["test_plain"], "test_plain_extra is recorded") == [
        "test_plain"
    ]


def test_only_test_files_are_checked():
    module = load_script()
    assert module.is_test_path("tests/test_x.py")
    assert module.is_test_path("tests/components/x.test.js")
    assert not module.is_test_path("src/tavle/x.py")
    assert not module.is_test_path("tests/fixtures/data.json")
