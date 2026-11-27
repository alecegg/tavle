"""Typed block renderers: classed HTML, escaping, error cards, no unsafe markup."""

from __future__ import annotations

import re

import pytest
from ui_fence import example_fence, ui_fence

from tavle import blocks
from tavle.page.render import render_page

HOSTILE = '<script>alert(1)</script>"><img src=x onerror=alert(1)>'
JSON_PROPS = re.compile(r'<script type="application/json">.*?</script>', re.DOTALL)
UNSAFE = [r"<script", r"style=", r"\son[a-z]+=", r"foreignObject"]


def page(lang: str, body: str, id_: str = "b1") -> str:
    return render_page(ui_fence(lang, body, id_), "t.md").body


def example_page(name: str, old: str = "", new: str = "") -> str:
    statement = (
        blocks.SPECS[name].example.replace(old, new)
        if old
        else blocks.SPECS[name].example
    )
    return render_page(example_fence(statement), "t.md").body


@pytest.mark.parametrize("name", blocks.TYPES)
def test_every_example_renders_classed_html(name):
    out = example_page(name)
    assert f'data-mithril="{name}"' in out
    assert "vb-error" not in out
    markup = re.sub(JSON_PROPS, "", out)  # a client block's props are data, not markup
    for pattern in UNSAFE:
        assert not re.search(pattern, markup), (name, pattern)


def test_hostile_every_field_escaped():
    model = (
        '[[entity]]\nname = "a<b>"\nkey = "id"\nfields = { id = "<i>x</i>" }\n'
        '[[entity.relations]]\nto = "a<b>"\nkind = "many-to-one"\n'
    )
    out = page("data-model", model)
    assert "a&lt;b&gt;" in out and "&lt;i&gt;" in out and "<i>" not in out
    endpoint = (
        'method = "GET"\npath = "/x<y>"\nauth = "<b>"\nsummary = "<u>"\n'
        'request = { "<k>" = "<v>" }\n[[responses]]\nstatus = 200\nbody = "<body>"\n'
    )
    out = page("endpoint", endpoint)
    for raw in ("<y>", "<b>", "<u>", "<k>", "<v>", "<body>"):
        assert raw not in out
    chart = (
        'kind = "line"\ntitle = "<t>"\nunit = "<u>"\nlabels = ["<l>"]\n'
        '[[series]]\nname = "<s>"\nvalues = [1]\n'
    )
    out = page("chart", chart)
    for raw in ("<t>", "<u>", "<l>", "<s>"):
        assert raw not in out
    states = (
        'screen = "<sc>"\n[empty]\nshows = "<e>"\n[loading]\nna = "<n>"\n'
        '[error]\nshows = "x"\n'
    )
    out = page("ui-states", states)
    for raw in ("<sc>", "<e>", "<n>"):
        assert raw not in out
    wire = 'title = "<w>"\ngrid = ["AB"]\n[regions]\nA = "<a>"\nB = "<b>"\n'
    out = page("wireframe", wire)
    assert "<a>" not in out and "<w>" not in out
    flow = 'title = "<f>"\n[[step]]\nid = "s"\ntext = "<x>"\nnext = ["s"]\n'
    out = page("flow", flow)
    assert "<f>" not in out and "<x>" not in out
    tbl = 'caption = "<c>"\ncolumns = ["<h>"]\nrows = [["<d>"], [3]]\n'
    out = page("table", tbl)
    for raw in ("<c>", "<h>", "<d>"):
        assert raw not in out


@pytest.mark.parametrize(
    ("name", "old", "new", "expected"),
    [
        ("data-model", "", "", '"kind": "many-to-one"'),
        ("endpoint", "", "", '"auth": "bearer"'),
        ("endpoint", '"bearer"', '"none"', '"auth": "none"'),
        ("chart", "", "", '"kind": "bar"'),
        ("chart", '"bar"', '"line"', "vb-line"),
        ("flow", "", "", '"desc": "flow of 4 steps, top to bottom"'),
    ],
)
def test_example_props_reach_the_page(name, old, new, expected):
    assert expected in example_page(name, old, new)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(
            ui_fence(
                "endpoint", 'method = "GET"\npath = "/x"\n[[responses]]\nstatus = 200\n'
            ),
            "missing-key",
            id="invalid-block",
        ),
        pytest.param(
            "```ui id=t\nt = table(columns: \n```\n", "ui block has", id="parse-error"
        ),
        pytest.param(
            "```table id=t\ncolumns = []\n```\n",
            "toml-fence-removed",
            id="old-typed-fence",
        ),
        pytest.param(
            '```ui id=c\nc = chart(kind: "bar", labels: ["a"], '
            'series: [{"name": "s", "values": ["x"]}])\n```\n',
            "series",
            id="non-number-chart-value",
        ),
    ],
)
def test_faulty_source_renders_an_error_card(source, expected):
    out = render_page(source, "t.md").body
    assert "vb-error" in out and expected in out


def test_negative_values_and_flat_series_render():
    body = (
        'kind = "bar"\nlabels = ["a", "b"]\n[[series]]\nname = "s"\nvalues = [-2, 3]\n'
    )
    assert "vb-bar" in page("chart", body)
    flat = 'kind = "line"\nlabels = ["a"]\n[[series]]\nname = "s"\nvalues = [0]\n'
    assert "vb-line" in page("chart", flat)


def test_error_card_escapes_hostile_text():
    text = f"t = table({HOSTILE.replace(chr(34), '')}: 1)\n"
    out = render_page(f"```ui id=t\n{text}```\n", "t.md").body
    assert "vb-error" in out
    assert "<script" not in out and "<img" not in out
