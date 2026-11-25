"""Component schemas and page validation."""

import pytest
from ui_fence import example_fence, statement_text, toml_props

from tavle import blocks
from tavle.blocks.spec import AnswerSchema, BlockSpec, PropertySpec
from tavle.blocks_render import COMPONENTS, render_block
from tavle.blocks_render.registry import PAGE_STATEMENTS
from tavle.lines import parse_lines
from tavle.page.page_check import check


def fenced(lang: str, body: str, id_: str = "b1", before: str = "") -> str:
    """A `ui` fence holding the statement for a TOML-written body."""
    statement = statement_text(id_, lang, toml_props(body))
    return f"{before}```ui id={id_}\n{statement}\n```\n"


MODEL = """[[entity]]
name = "a"
key = "id"
fields = { id = "uuid" }
"""


ENDPOINT = 'method = "GET"\npath = "/x"\n[[responses]]\nstatus = 200\n'


def rules(doc: str) -> list[str]:
    return [e.rule for e in check(doc)]


def messages(doc: str) -> str:
    return "\n".join(e.message for e in check(doc))


def test_all_types_registered():
    assert blocks.TYPES == (
        "chart",
        "data-model",
        "decision",
        "endpoint",
        "flow",
        "table",
        "ui-states",
        "wireframe",
    )


@pytest.mark.parametrize("name", blocks.TYPES)
def test_each_example_is_valid(name):
    assert check(example_fence(blocks.SPECS[name].example)) == []


def test_data_model_missing_relation_target():
    body = MODEL + '[[entity.relations]]\nto = "ghost"\nkind = "one-to-one"\n'
    doc = fenced("data-model", body)
    assert rules(doc) == ["relation-target"]
    assert "ghost" in messages(doc)


def test_data_model_missing_key_and_undeclared_key_field():
    no_key = '[[entity]]\nname = "a"\nfields = { id = "uuid" }\n'
    assert "missing-key" in rules(fenced("data-model", no_key))
    bad_key = '[[entity]]\nname = "a"\nkey = "nope"\nfields = { id = "uuid" }\n'
    assert rules(fenced("data-model", bad_key)) == ["entity-key"]


def test_data_model_duplicate_entity():
    assert rules(fenced("data-model", MODEL + MODEL)) == ["entity-duplicate"]


def test_endpoint_without_auth_is_an_error():
    doc = fenced("endpoint", ENDPOINT)
    assert rules(doc) == ["missing-key"]
    assert "'auth'" in messages(doc)


def test_endpoint_explicit_none_accepted():
    assert check(fenced("endpoint", 'auth = "none"\n' + ENDPOINT)) == []


def test_endpoint_bad_status_method_path():
    body = 'auth = "none"\nmethod = "FETCH"\npath = "x"\n[[responses]]\nstatus = 99\n'
    assert rules(fenced("endpoint", body)) == ["type", "type", "type"]


def test_ui_states_requires_three_states():
    body = '[empty]\nshows = "x"\n'
    doc = fenced("ui-states", body)
    assert rules(doc) == ["ui-state-missing", "ui-state-missing"]
    assert "loading" in messages(doc) and "error" in messages(doc)


def test_ui_states_na_needs_reason_and_exactly_one_form():
    ok = '[empty]\nna = "static page"\n[loading]\nshows = "s"\n[error]\nshows = "e"\n'
    assert check(fenced("ui-states", ok)) == []
    both = ok.replace('na = "static page"', 'na = "r"\nshows = "x"')
    assert rules(fenced("ui-states", both)) == ["state-form"]
    blank = ok.replace('"static page"', '""')
    assert rules(fenced("ui-states", blank)) == ["type"]


def test_wireframe_region_cross_references_and_width():
    body = 'grid = ["AB", "A"]\n[regions]\nA = "a"\nC = "c"\n'
    assert sorted(rules(fenced("wireframe", body))) == [
        "grid-width",
        "region-undeclared",
        "region-unused",
    ]


def test_flow_unknown_step_and_duplicate_step():
    body = (
        '[[step]]\nid = "a"\ntext = "t"\nnext = ["z"]\n[[step]]\nid = "a"\ntext = "t"\n'
    )
    assert sorted(rules(fenced("flow", body))) == ["step-duplicate", "step-target"]


def test_table_row_width_and_chart_series_length():
    table = 'columns = ["a", "b"]\nrows = [["1"], ["1", "2"]]\n'
    assert rules(fenced("table", table)) == ["row-width"]
    chart = 'kind = "pie"\nlabels = ["x", "y"]\n[[series]]\nname = "s"\nvalues = [1]\n'
    assert sorted(rules(fenced("chart", chart))) == ["series-length", "type"]


def test_unknown_key_is_reported():
    assert rules(fenced("table", 'columns = ["a"]\nrows = [["1"]]\nbogus = 1\n')) == [
        "unknown-key"
    ]


def test_covers_is_reserved_and_validated():
    ok = 'covers = ["order", "post-orders"]\ncolumns = ["a"]\nrows = [["1"]]\n'
    assert check(fenced("table", ok)) == []
    bad = 'covers = "order"\ncolumns = ["a"]\nrows = [["1"]]\n'
    assert rules(fenced("table", bad)) == ["covers"]


def test_ill_formed_ids():
    body = 'columns = ["a"]\nrows = [["1"]]\n'
    for bad in ("Order", "1a", "a_b", "a" * 49):
        assert "id-invalid" in rules(fenced("table", body, bad)), bad
    assert check(fenced("table", body, "a" * 48)) == []


def test_duplicate_id_names_first_line():
    body = 'columns = ["a"]\nrows = [["1"]]\n'
    doc = fenced("table", body, "t") + "\n" + fenced("table", body, "t")
    errors = check(doc)
    assert [e.rule for e in errors] == ["id-duplicate"]
    assert errors[0].line == 9 and "line 2" in errors[0].message
    assert (errors[0].statement_id, errors[0].path) == ("t", "")


def test_property_faults_carry_statement_id_and_path():
    doc = fenced("table", 'columns = ["a"]\nrows = 3\n', "t1")
    (error,) = check(doc)
    assert (error.rule, error.statement_id, error.path) == ("type", "t1", "rows")
    assert error.text() == f"line {error.line}: type: {error.message}"


def test_widget_validator_faults_have_no_path_but_keep_the_statement_id():
    doc = fenced("table", 'columns = ["a"]\nrows = [["1", "2"]]\n', "t2")
    (error,) = check(doc)
    assert (error.rule, error.statement_id, error.path) == ("row-width", "t2", "")


@pytest.mark.parametrize("lang", sorted({*blocks.SPECS, "recap", "deps"}))
def test_old_typed_fence_is_a_removed_error(lang):
    errors = check(f"```{lang} id=x\nanything\n```\n")
    assert [e.rule for e in errors] == ["toml-fence-removed"]
    assert "the block catalog lists the components" in errors[0].message


def test_indented_fence_and_untyped_fences_are_handled():
    doc = "```python\n```ui id=x\nnot a statement\n```\n"
    assert check(doc) == []  # a fence inside another fence is text
    ok = '- item\n\n  ```ui id=t\n  t = table(columns: ["a"], rows: [["1"]])\n  ```\n'
    assert check(ok) == []


def _example_data(name):
    (statement,) = parse_lines(blocks.COMPONENT_SPECS[name].example).statements
    return statement.props


def test_components_cover_every_spec_with_props_and_example():
    assert set(COMPONENTS) == set(blocks.COMPONENT_SPECS)
    assert {"recap", "deps", "decision", "chart"} <= set(COMPONENTS)
    for name, component in COMPONENTS.items():
        assert component.spec is blocks.COMPONENT_SPECS[name]
        if name in PAGE_STATEMENTS:
            continue
        out = render_block(name, _example_data(name), "id1", 1)
        assert f'data-mithril="{name}"' in out and "vb-error" not in out


def test_deps_props_are_the_layout_of_their_edges():
    from tavle.graph import deps_layout

    props = COMPONENTS["deps"].props
    assert props is not None
    assert props(_example_data("deps")) == deps_layout(
        {"a": [], "b": ["a"], "c": ["a", "b"]}, {"a": "done", "b": "in progress"}
    )


def test_decision_answer_schema():
    data = _example_data("decision")
    answer_schema = COMPONENTS["decision"].answer_schema
    assert answer_schema is not None
    schema = answer_schema(data)
    assert schema == AnswerSchema(
        "verdict", ("text",), ("approved", "denied", "commented")
    )
    narrowed = answer_schema({**data, "options": ["approve"]})
    assert narrowed is not None and narrowed.allowed == ("approved",)
    answering = {"decision", "choice", "form", "comment", "ranking", "slider"}
    assert all(
        c.answer_schema is None for n, c in COMPONENTS.items() if n not in answering
    )


def test_deps_nodes_carry_their_status_in_the_tooltip():
    from tavle.graph import deps_layout

    nodes = deps_layout({"a": [], "b": ["a"]}, {"b": "blocked"})["nodes"]
    assert isinstance(nodes, list)
    by_label = {n["label"]: n for n in nodes}
    assert by_label["b"]["status"] == "blocked"
    assert by_label["b"]["title"] == "b: blocked"
    assert "status" not in by_label["a"]


def test_deps_and_recap_validation():
    assert blocks.check_props("deps", {"edges": {"a": "b"}}, 1)
    assert blocks.check_props("deps", {"edges": {"a:b": []}}, 1)
    assert blocks.check_props("deps", {}, 1)
    edges = {"a": [], "b": ["a"]}
    assert not blocks.check_props("deps", {"edges": edges, "status": {"a": "done"}}, 1)
    assert blocks.check_props("deps", {"edges": edges, "status": {"z": "done"}}, 1)
    assert blocks.check_props("deps", {"edges": edges, "status": {"a": 1}}, 1)
    assert blocks.check_props("recap", {"rows": [{"file": "a"}]}, 1)
    assert blocks.check_props("recap", {}, 1)


def test_property_metadata_construction_and_defaults():
    prop = PropertySpec("title", "string")
    assert (prop.required, prop.enum, prop.items, prop.fields) == (False, (), None, ())
    detailed = PropertySpec("choice", "string", True, ("yes", "no"))
    spec = BlockSpec("test", "summary", (), "", lambda _: [], properties=(detailed,))
    assert spec.properties == (detailed,)
    assert BlockSpec("t", "", (), "", lambda _: []).properties == ()


def test_generic_property_validation(monkeypatch):
    spec = BlockSpec(
        "test",
        "",
        (),
        "",
        lambda _: [],
        properties=(
            PropertySpec("title", "string", required=True, enum=("yes",)),
            PropertySpec(
                "fields",
                "list",
                items="object",
                fields=(PropertySpec("label", "id", required=True),),
            ),
            PropertySpec("span", "any"),
        ),
    )
    monkeypatch.setitem(blocks.COMPONENT_SPECS, "test", spec)
    assert (
        blocks.check_props(
            "test", {"title": "yes", "fields": [{"label": "valid-id"}]}, 1
        )
        == []
    )
    errors = blocks.check_props(
        "test", {"extra": 1, "fields": [{"label": "Bad", "other": 1}, {}]}, 1
    )
    assert {e.rule for e in errors} == {"unknown-key", "missing-key", "type"}
    assert any("fields[1].label" in e.message for e in errors)
    assert blocks.check_props("test", {"title": "no"}, 1)[0].rule == "type"
    located = {
        (e.rule, e.path)
        for e in blocks.check_props(
            "test", {"extra": 1, "fields": [{"label": "Bad", "other": 1}, {}]}, 1, "t1"
        )
    }
    assert located == {
        ("unknown-key", "extra"),
        ("type", "fields[1].label"),
        ("unknown-key", "fields[1].other"),
        ("missing-key", "title"),
        ("missing-key", "fields[2].label"),
    }
    for span in (3, "2-4", [1, 2]):
        assert blocks.check_props("test", {"title": "yes", "span": span}, 1) == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"type": "string", "items": "string"},
        {"type": "integer", "enum": ("a",)},
        {"type": "any", "enum": ("a",)},
        {"type": "any", "items": "string"},
        {"type": "list", "items": "integer", "enum": ("a",)},
        {"type": "string", "fields": (PropertySpec("x", "string"),)},
        {"type": "list", "items": "string", "fields": (PropertySpec("x", "string"),)},
        {"type": "integer", "nonempty": True},
    ],
)
def test_property_metadata_rejects_impossible_combinations(kwargs):
    with pytest.raises(ValueError):
        PropertySpec("p", **kwargs)


def test_nonempty_rejects_a_blank_string_and_an_empty_list_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = BlockSpec(
        "test",
        "test",
        ("title", "tags"),
        "test = test()",
        lambda _: [],
        properties=(
            PropertySpec("title", "string", nonempty=True),
            PropertySpec("tags", "list", items="string", nonempty=True),
        ),
    )
    monkeypatch.setitem(blocks.COMPONENT_SPECS, "test", spec)
    assert blocks.check_props("test", {"title": "t", "tags": [""]}, 1) == []
    errors = blocks.check_props("test", {"title": "  ", "tags": []}, 1)
    assert [e.message for e in errors] == [
        "'title' must not be empty",
        "'tags' must not be empty",
    ]


def test_extra_keys_check_each_unnamed_key_against_one_property(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = PropertySpec(
        "state", "object", fields=(PropertySpec("shows", "string", nonempty=True),)
    )
    spec = BlockSpec(
        "test",
        "test",
        ("screen", "<state>"),
        "test = test()",
        lambda _: [],
        properties=(PropertySpec("screen", "string"),),
        extra_keys=state,
    )
    monkeypatch.setitem(blocks.COMPONENT_SPECS, "test", spec)
    assert blocks.check_props("test", {"screen": "s", "empty": {"shows": "x"}}, 1) == []
    errors = blocks.check_props("test", {"empty": "x", "busy": {"shows": ""}}, 1)
    assert [e.message for e in errors] == [
        "'busy.shows' must not be empty",
        "'empty' must be object",
    ]
