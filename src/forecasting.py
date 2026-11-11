"""Demand forecasting for the supply chain simulator (SCM-F-024, SCM-F-025).

Moving average and demand standard deviation (SCM-F-024), plus exponential
smoothing and the MAE and MAPE forecast error measures (SCM-F-025).
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



def _check_series(actual: list, forecast: list) -> tuple:
    """Validate both series with _check_history and require the same length."""
    actual_values = _check_history(actual)
    forecast_values = _check_history(forecast)
    if len(actual_values) != len(forecast_values):
        raise ValueError(
            f"actual and forecast must be the same length, got {len(actual_values)} and {len(forecast_values)}"
        )
    return actual_values, forecast_values


def exponential_smoothing(history: list, alpha: float) -> float:
    """Exponential smoothing forecast (SCM-F-025).

    Start with F = first value, then for each actual A: F = alpha x A + (1 - alpha) x F.
    Returns the final F.
    """
    if (isinstance(alpha, bool) or not isinstance(alpha, (int, float))
            or not 0 < alpha <= 1):
        raise ValueError(f"alpha must be above 0 and at most 1, got {alpha!r}")
    values = _check_history(history)
    forecast = values[0]
    for actual in values:
        forecast = alpha * actual + (1 - alpha) * forecast
    return forecast


def mean_absolute_error(actual: list, forecast: list) -> float:
    """Average of |actual - forecast| over all periods."""
    actual, forecast = _check_series(actual, forecast)
    return sum(abs(a - f) for a, f in zip(actual, forecast)) / len(actual)


def mean_absolute_percentage_error(actual: list, forecast: list) -> float:
    """Average of |actual - forecast| / actual, in percent; periods where actual is 0 are skipped."""
    actual, forecast = _check_series(actual, forecast)
    pairs = [(a, f) for a, f in zip(actual, forecast) if a != 0]
    if not pairs:
        raise ValueError("MAPE needs at least one period where actual is not 0")
    return 100 * sum(abs(a - f) / abs(a) for a, f in pairs) / len(pairs)