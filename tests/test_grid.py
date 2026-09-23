from collections import Counter

from trolley.grid import Cell, cells_for_model, samples_for

N = 4


def test_panel_models_get_four_samples_and_jev_gets_two():
    assert samples_for("opus5") == 4
    assert samples_for("grok43") == 4
    assert samples_for("jev") == 2


def test_jev_grid_is_half_the_size():
    assert len(list(cells_for_model("jev", samples=samples_for("jev")))) == 12 * 5 * 2


def test_cell_count_is_rungs_times_angles_times_samples():
    cells = list(cells_for_model("opus5", samples=N))
    assert len(cells) == 12 * 5 * N


def test_cells_are_unique():
    cells = list(cells_for_model("opus5", samples=N))
    ids = {(c.model_key, c.rung.key, c.angle.key, c.sample_idx) for c in cells}
    assert len(ids) == len(cells)


def test_option_order_is_balanced_within_every_cell_group():
    cells = list(cells_for_model("opus5", samples=N))
    grouped = Counter()
    for c in cells:
        if c.option_a_is_act:
            grouped[(c.rung.key, c.angle.key)] += 1
    assert set(grouped.values()) == {N // 2}
    assert len(grouped) == 60


def test_odd_sample_counts_are_rejected():
    import pytest
    with pytest.raises(ValueError):
        list(cells_for_model("opus5", samples=3))
