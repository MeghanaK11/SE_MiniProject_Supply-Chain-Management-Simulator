"""Demand forecasting for the supply chain simulator (SCM-F-024).

Exponential smoothing and forecast error measures (SCM-F-025) are added to
this module in a later backlog item.
"""
import math
import statistics


def _check_history(history) -> list:
    """Validate a demand history and return it as a list."""
    if not isinstance(history, (list, tuple)) or len(history) == 0:
        raise ValueError("history must be a non-empty list of numbers")
    for value in history:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"history values must be finite numbers, got {value!r}")
    return list(history)


def _check_window(window) -> int:
    """Validate a forecast window size."""
    if isinstance(window, bool) or not isinstance(window, int) or window < 1:
        raise ValueError(f"window must be an integer of at least 1, got {window!r}")
    return window


def moving_average(history, window: int) -> float:
    """Average of the last `window` values; uses all values if history is shorter."""
    values = _check_history(history)
    size = _check_window(window)
    recent = values[-size:]
    return sum(recent) / len(recent)


def demand_std(history, window: int) -> float:
    """Population standard deviation of the last `window` values; 0.0 if fewer than 2."""
    values = _check_history(history)
    size = _check_window(window)
    recent = values[-size:]
    if len(recent) < 2:
        return 0.0
    return statistics.pstdev(recent)
