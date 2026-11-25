"""Progress cell validation."""

from tavle.blocks.tables import validate_table


def test_progress_cells():
    data = {
        "columns": ["Progress"],
        "types": {"Progress": "progress"},
        "rows": [[[1, 2]], [[3, 6]], [[0, 0]]],
    }
    assert validate_table(data) == []


def test_bad_progress_cells():
    for cell in ([5, 3], "5", [-1, 2], [1.5, 2], [True, 2]):
        data = {
            "columns": ["Progress"],
            "types": {"Progress": "progress"},
            "rows": [[cell]],
        }
        faults = validate_table(data)
        assert len(faults) == 1
        assert faults[0].rule == "type"
        assert "rows[1] 'Progress'" in faults[0].message
