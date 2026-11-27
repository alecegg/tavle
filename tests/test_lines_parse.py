"""Line syntax parser: valid cases, every error site, recovery, partial input."""

import pytest

from tavle.lines import ParseError, Ref, parse_lines
from tavle.lines.grammar import EXAMPLES

# A parser that stops advancing must fail the test, not hang the run.
pytestmark = pytest.mark.timeout(2, method="signal")

_NOT_CLOSED_AT_END = "statement is not closed before the end of the text"
_BAD_ESCAPE = "bad string escape: Invalid \\escape: line 1 column "


@pytest.mark.parametrize("example", EXAMPLES)
def test_pinned_examples_parse(example):
    result = parse_lines(example)
    assert result.errors == []
    assert result.statements


def test_values_of_every_type():
    text = (
        'a = chart(s: "x\\ny", i: 3, f: -1.5, e: 1e2, E: 1E2, t: true, n: null,'
        ' arr: [1, [2]], obj: {"k": {bare: false}})'
    )
    (stmt,) = parse_lines(text).statements
    assert (stmt.id, stmt.component, stmt.line) == ("a", "chart", 1)
    assert stmt.props == {
        "s": "x\ny",
        "i": 3,
        "f": -1.5,
        "e": 100.0,
        "E": 100.0,
        "t": True,
        "n": None,
        "arr": [1, [2]],
        "obj": {"k": {"bare": False}},
    }
    assert isinstance(stmt.props["i"], int)


def test_refs_resolve_at_any_nesting():
    text = "a = flow()\nb = flow(x: [a, [a]], y: {k: a, j: {k: a}}, z: [{k: a}])"
    result = parse_lines(text)
    assert result.errors == []
    ref = Ref("a")
    assert result.statements[1].props == {
        "x": [ref, [ref]],
        "y": {"k": ref, "j": {"k": ref}},
        "z": [{"k": ref}],
    }


def test_commas_need_no_space():
    result = parse_lines("a = flow(x:[1,2],y:{k:1,j:2})")
    assert result.errors == []
    assert result.statements[0].props == {"x": [1, 2], "y": {"k": 1, "j": 2}}


def test_reference_and_multiline_and_comments():
    text = (
        "# top\n"
        "a = flow(x: 1)  # trailing\n"
        "\n"
        "b = table(\n"
        "  src: a,   # ref\n"
        "  rows: [\n"
        "    1,\n"
        "    2,\n"
        "  ],\n"
        ")\n"
    )
    result = parse_lines(text)
    assert result.errors == []
    a, b = result.statements
    assert (a.line, a.end_line, b.line, b.end_line) == (2, 2, 4, 10)
    assert b.props == {"src": Ref("a"), "rows": [1, 2]}


def test_unicode_and_hash_inside_string():
    (stmt,) = parse_lines('a = recap(t: "héllo # 日本 \\u00e9")').statements
    assert stmt.props["t"] == "héllo # 日本 é"


@pytest.mark.parametrize(
    ("empty", "wrap"),
    [("[]", "[{}]"), ("{}", "{{k: {}}}")],
    ids=["array", "object"],
)
def test_nesting_stops_after_32_levels(empty, wrap):
    value = empty
    for _ in range(31):
        value = wrap.format(value)
    assert parse_lines(f"a = flow(x: {value})").errors == []
    result = parse_lines(f"a = flow(x: {wrap.format(value)})")
    assert result.errors == [ParseError(1, "depth", "nesting deeper than 32")]


@pytest.mark.parametrize("text", ["", "# only\n\n", "# no newline at the end"])
def test_empty_and_comment_only(text):
    result = parse_lines(text)
    assert (result.statements, result.errors) == ([], [])


@pytest.mark.parametrize(
    ("text", "rule", "line", "message"),
    [
        ("A = flow()", "id-invalid", 1, "id 'A' must match ^[a-z][a-z0-9-]{0,47}$"),
        ("true = flow()", "id-invalid", 1, "id 'true' is a reserved literal"),
        ("false = flow()", "id-invalid", 1, "id 'false' is a reserved literal"),
        ("null = flow()", "id-invalid", 1, "id 'null' is a reserved literal"),
        (
            "a = flow()\nb = flow()\na = flow()",
            "id-duplicate",
            3,
            "id 'a' is already used at line 1",
        ),
        ("\n\na = flow(x: 1, x: 2)", "prop-duplicate", 3, "duplicate prop 'x'"),
        ('a = flow(o: {"k": 1, "k": 2})', "prop-duplicate", 1, "duplicate key 'k'"),
        ("a = flow(x: b)", "ref-unknown", 1, "'b' is not an earlier statement"),
        ("a = flow(x: a)", "ref-unknown", 1, "'a' is not an earlier statement"),
        ("a = flow() x", "trailing", 1, "text after the closing ')'"),
        ("a = flow()\nb = flow() x", "trailing", 2, "text after the closing ')'"),
        ("(x)", "syntax", 1, "expected '<id> = Component(...)', found '('"),
        ("a flow()", "syntax", 1, "expected '=' after the id, found 'f'"),
        ("a = (x: 1)", "syntax", 1, "expected a component name after '='"),
        ("a = flow x", "syntax", 1, "expected '(' after the component name, found 'x'"),
        ("a = flow(1: 2)", "syntax", 1, "expected a prop name, found '1'"),
        ("a = flow(x 1)", "syntax", 1, "expected ':' after prop name, found '1'"),
        (
            "a = flow(\n  x: 1\n  y: 2\n)",
            "syntax",
            3,
            "expected ',' or ')' after value",
        ),
        ("a = flow(x: 01)", "syntax", 1, "expected ',' or ')' after value"),
        ("a = flow(x: [1 2])", "syntax", 1, "expected ',' or ']' in array"),
        ("a = flow(x: {k: 1 j: 2})", "syntax", 1, "expected ',' or '}' in object"),
        ("a = flow(x: {1: 2})", "syntax", 1, "expected an object key"),
        ("a = flow(x: {k 1})", "syntax", 1, "expected ':' after key, found '1'"),
        ("a = flow(x: @)", "syntax", 1, "unexpected '@'"),
        ("a = flow(x: -)", "syntax", 1, "bad number"),
        ("a = flow(x: 1e999)", "syntax", 1, "number is out of range"),
        pytest.param(
            "a = flow(x: " + "9" * 5000 + ")",
            "syntax",
            1,
            "integer has too many digits",
            id="huge-integer",
        ),
        ('a = flow(x: "bad \\q")', "syntax", 1, _BAD_ESCAPE + "6 (char 5)"),
        # A backslash can carry a string onto the next line; report where it starts.
        ('a = flow(x: "q\\\n")', "syntax", 1, _BAD_ESCAPE + "3 (char 2)"),
        (
            'a = flow(x: "a\tb")',
            "syntax",
            1,
            "raw control character in string (use an escape such as \\t)",
        ),
        ('a = flow(x: "\\ud800")', "syntax", 1, "lone surrogate escape in string"),
        ('a = flow(x: "\\udfff")', "syntax", 1, "lone surrogate escape in string"),
        (
            'a = flow(\n  x: "open\n)',
            "unterminated",
            2,
            "string is not closed on its line",
        ),
        ("a = flow(x: 1", "unterminated", 1, _NOT_CLOSED_AT_END),
        ("ok = flow()\n\nb = flow(x: [", "unterminated", 3, _NOT_CLOSED_AT_END),
    ],
)
def test_error_classes_have_lines(text, rule, line, message):
    result = parse_lines(text)
    assert result.errors == [ParseError(line, rule, message)]
    assert all(statement.line != line for statement in result.statements)


def test_error_text_and_recovery():
    text = "a = flow(x: )\nb = flow(y: 2)\nc = flow(z: ]\nd = flow()"
    result = parse_lines(text)
    assert [e.line for e in result.errors] == [1, 3]
    assert [s.id for s in result.statements] == ["b", "d"]
    assert result.errors[0].text().startswith("line 1: syntax: ")


@pytest.mark.parametrize(
    ("text", "kept"),
    [
        ("a = flow(x: 1\nb = flow()\nc = flow()", ["b", "c"]),
        ('a = flow(x: [1],\n  y: "s"\nb = flow()', ["b"]),
    ],
)
def test_missing_close_paren_does_not_swallow_next_statement(text, kept):
    result = parse_lines(text)
    message = "statement is not closed before the next statement"
    assert result.errors == [ParseError(1, "unterminated", message)]
    assert [s.id for s in result.statements] == kept


@pytest.mark.parametrize(
    "tail", ["b = table(rows: [1, 2,", 'b = table(rows: [1, 2,\n  "x']
)
def test_partial_tail_is_pending_not_error(tail):
    text = f"a = flow(x: 1)\n{tail}"
    partial = parse_lines(text, partial=True)
    assert partial.errors == []
    assert [s.id for s in partial.statements] == ["a"]
    assert partial.pending == tail
    strict = parse_lines(text)
    assert strict.errors == [ParseError(2, "unterminated", _NOT_CLOSED_AT_END)]
    assert [s.id for s in strict.statements] == ["a"]
    assert strict.pending == ""


@pytest.mark.parametrize(
    ("text", "rule", "kept", "pending"),
    [
        ("A = flow()\nb = fl", "id-invalid", [], "b = fl"),
        ("a = flow()\nb = x(t: nope)\nc = fl", "ref-unknown", ["a"], "c = fl"),
    ],
)
def test_partial_still_reports_real_errors(text, rule, kept, pending):
    result = parse_lines(text, partial=True)
    assert [e.rule for e in result.errors] == [rule]
    assert [s.id for s in result.statements] == kept
    assert result.pending == pending


def test_partial_complete_text_has_no_pending():
    result = parse_lines("a = flow()\n", partial=True)
    assert result.pending == ""
    assert [s.id for s in result.statements] == ["a"]


def test_no_dynamic_evaluation():
    result = parse_lines('a = flow(x: __import__("os"))')
    assert [e.rule for e in result.errors] == ["syntax"]
    assert result.statements == []


@pytest.mark.parametrize(
    "tail",
    ["tru", "b", "1.", "1e", "1e+", "1e999", "-", '"abc', '"ab\\', "[1, tr"],
)
def test_partial_mid_token_cutoff_is_pending(tail):
    text = f"b = flow()\na = table(x: {tail}"
    result = parse_lines(text, partial=True)
    assert result.errors == []
    assert [s.id for s in result.statements] == ["b"]
    assert result.pending == f"a = table(x: {tail}"


@pytest.mark.parametrize("tail", ["a", "a ", "a =", "a = ", "a = fl", "a = flow"])
def test_partial_cutoff_before_open_paren_is_pending(tail):
    result = parse_lines(tail, partial=True)
    assert result.errors == []
    assert result.pending == tail


def test_hyphenated_component_names_and_refs():
    text = "my-model = data-model(a: 1)\nscreens = ui-states(of: my-model)"
    result = parse_lines(text)
    assert result.errors == []
    assert [s.component for s in result.statements] == ["data-model", "ui-states"]
    assert result.statements[1].props == {"of": Ref("my-model")}
