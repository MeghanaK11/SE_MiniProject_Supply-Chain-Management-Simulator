import pytest

from src.forecasting import (
    demand_std,
    exponential_smoothing,
    mean_absolute_error,
    mean_absolute_percentage_error,
    moving_average,
)


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




def test_exponential_smoothing_known_value():
    """TC-FC-06: [10, 20, 30] with alpha 0.5 gives 22.5; alpha 1 returns the last value."""
    assert exponential_smoothing([10, 20, 30], 0.5) == pytest.approx(22.5)
    assert exponential_smoothing([10, 20, 30], 1) == pytest.approx(30)
    assert exponential_smoothing([7], 0.3) == pytest.approx(7)


@pytest.mark.parametrize("bad_alpha", [0, 1.5, -0.2, True, "0.5"])
def test_exponential_smoothing_invalid_alpha(bad_alpha):
    """TC-FC-07: alpha 0 and 1.5 (and other values outside 0 < alpha <= 1) raise ValueError; so do empty or bad histories."""
    with pytest.raises(ValueError, match="alpha"):
        exponential_smoothing([10, 20, 30], bad_alpha)
    for bad_history in ([], [10, "20"], [10, float("nan")], [True, 5], [10, float("inf")]):
        with pytest.raises(ValueError, match="history"):
            exponential_smoothing(bad_history, 0.5)


def test_mae():
    """TC-FC-08: actual [10, 20], forecast [12, 18] gives 2.0."""
    assert mean_absolute_error([10, 20], [12, 18]) == pytest.approx(2.0)


def test_mape():
    """TC-FC-09: the same data gives 15.0 percent; zero actuals are skipped; all zeros raise ValueError."""
    assert mean_absolute_percentage_error([10, 20], [12, 18]) == pytest.approx(15.0)
    assert mean_absolute_percentage_error([10, 0, 20], [12, 5, 18]) == pytest.approx(15.0)
    with pytest.raises(ValueError):
        mean_absolute_percentage_error([0, 0], [1, 2])


@pytest.mark.parametrize("func", [mean_absolute_error, mean_absolute_percentage_error])
def test_error_length_mismatch(func):
    """TC-FC-10: lengths 2 and 3 raise ValueError; so do empty lists and NaN, text or bool values."""
    with pytest.raises(ValueError, match="same length"):
        func([10, 20], [10, 20, 30])
    with pytest.raises(ValueError, match="empty"):
        func([], [])
    for actual, forecast in (([10, float("nan")], [1, 2]), ([10, 20], [12, "18"]), ([True, 20], [12, 18])):
        with pytest.raises(ValueError):
            func(actual, forecast)