import pytest

from src.forecasting import demand_std, moving_average


def test_moving_average_window():
    """TC-FC-01: history 10, 20, 30, 40 with window 2 gives 35.0."""
    assert moving_average([10, 20, 30, 40], 2) == 35.0


def test_moving_average_short_history():
    """TC-FC-02: a history shorter than the window uses all values."""
    assert moving_average([10, 20], 7) == 15.0


@pytest.mark.parametrize("history, window", [
    ([10, 20], 0),
    ([10, 20], -1),
    ([10, 20], 2.5),
    ([10, 20], True),
    ([], 3),
    (None, 3),
    ([10, "20"], 2),
    ([10, float("nan")], 2),
    ([10, True], 2),
])
def test_moving_average_invalid(history, window):
    """TC-FC-03: a window below 1, an empty history or non-numeric values raise ValueError."""
    with pytest.raises(ValueError):
        moving_average(history, window)
    with pytest.raises(ValueError):
        demand_std(history, window)


def test_demand_std():
    """TC-FC-04: population std of 10, 20, 30, 40 over window 4 is about 11.18; window 2 uses the last two."""
    assert demand_std([10, 20, 30, 40], 4) == pytest.approx(11.1803, abs=1e-4)
    assert demand_std([10, 20, 30, 40], 2) == pytest.approx(5.0)


def test_demand_std_single_value():
    """TC-FC-05: fewer than two values in the window gives 0.0."""
    assert demand_std([10], 4) == 0.0
    assert demand_std([10, 20, 30], 1) == 0.0
