"""Streaming: complete-statement prefix is stable at every cut offset."""

import pytest

from tavle.lines import parse_lines
from tavle.lines.grammar import EXAMPLES

# A parser that stops advancing must fail the test, not hang the run.
pytestmark = pytest.mark.timeout(2, method="signal")

PAGE = (
    'model = data-model(name: "User", note: "a \\"q\\" # not a comment")\n'
    "states = ui-states(of: model)  # trailing\n"
    "# comment line\n"
    "speed = slider(min: 0, max: 1.5, step: 0.5, value: -1e2)\n"
    'pick = choice(\n  question: "Which?",\n  options: ["x", "y"],  # why\n'
    '  multi: false,\n  extra: {"k": null, v: [1, 2.5, true]},\n)\n'
    "note = comment(target: pick, text: null)\n"
    'plan-deps = deps(edges: {"b": ["a"], "c": ["a", "b"]})\n'
)


@pytest.mark.parametrize(
    "text", [PAGE, *EXAMPLES], ids=["page", *map(str, range(len(EXAMPLES)))]
)
def test_every_offset_is_prefix_stable_and_never_raises(text):
    full = parse_lines(text)
    assert full.errors == []
    previous: list = []
    for cut in range(len(text) + 1):
        result = parse_lines(text[:cut], partial=True)
        assert result.errors == [], (cut, text[:cut][-30:])
        assert result.statements == full.statements[: len(result.statements)], cut
        assert len(result.statements) >= len(previous), cut  # never shrinks
        previous = result.statements
    assert previous == full.statements
