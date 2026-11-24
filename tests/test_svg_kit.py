"""Pure helpers of the shared SVG kit."""

from tavle.blocks_render import svg


def test_series_differentiators_cycle_and_differ() -> None:
    shapes = [svg.marker_shape(i) for i in range(6)]
    dashes = [svg.dash(i) for i in range(6)]
    assert len(set(shapes)) == 6 and len(set(dashes)) == 6
    assert svg.marker_shape(6) == shapes[0] and svg.dash(7) == dashes[1]
    assert dashes[0] == ""


def test_wrap_text_respects_budget() -> None:
    assert svg.wrap_text("one two three four", 9) == ["one two", "three", "four"]
    assert svg.wrap_text("abcdefghij", 4) == ["abcd", "efgh", "ij"]
    assert svg.wrap_text("", 5) == []
    assert svg.wrap_text("a b", 0) == ["a", "b"]
    for line in svg.wrap_text("the quick brown fox jumps over", 8):
        assert len(line) <= 8


def test_copy_attr_escapes_quotes() -> None:
    assert svg.copy_attr('say "hi" <b>') == ' data-copy="say &quot;hi&quot; &lt;b&gt;"'
