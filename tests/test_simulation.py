
"""Tests for Simulation Engine v2."""

import copy
import json
from pathlib import Path

import pytest

from src.simulation import run_simulation


CONFIG_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "sample_config.json"
)


def load_sample_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


# --------------------------------------------------
# B-19: Simulation Engine MVP tests
# TC-SIM-01 to TC-SIM-04
# --------------------------------------------------

def test_simulation_produces_90_daily_records():
    """TC-SIM-01: 30 days and 3 products produce 90 records."""
    result = run_simulation(load_sample_config())

    assert len(result.daily_records) == 90


def test_simulation_inventory_and_fulfilment_constraints():
    """
    TC-SIM-02: Stock and backorders never go negative;
    total shipped never exceeds total demand.
    """
    result = run_simulation(load_sample_config())

    for record in result.daily_records:
        assert record["stock_end"] >= 0
        assert record["backorder"] >= 0
        assert record["shipped"] >= 0

    total_shipped = sum(
        record["shipped"]
        for record in result.daily_records
    )
    total_demand = sum(
        record["demand"]
        for record in result.daily_records
    )

    assert total_shipped <= total_demand


def test_simulation_is_deterministic_with_same_seed():
    """TC-SIM-03: Same seed produces identical daily records."""
    config = load_sample_config()

    first_result = run_simulation(copy.deepcopy(config))
    second_result = run_simulation(copy.deepcopy(config))

    assert first_result.daily_records == second_result.daily_records


def test_low_initial_stock_for_p003_triggers_purchase_order():
    """TC-SIM-04: Low P-003 stock results in a PO_PLACED event."""
    config = load_sample_config()

    config["warehouse"]["initial_stock"]["P-003"] = 0

    result = run_simulation(config)

    p003_po_events = [
        event
        for event in result.events
        if event["type"] == "PO_PLACED"
        and "P-003" in event["message"]
    ]

    assert len(p003_po_events) >= 1


# --------------------------------------------------
# B-30: Simulation Engine v2 tests
# TC-SIM-07 to TC-SIM-10
# --------------------------------------------------

def test_simulation_records_all_cost_categories():
    """TC-SIM-07: All cost categories should be present and totalled."""
    result = run_simulation(load_sample_config())

    expected_keys = {
        "holding",
        "stockout",
        "ordering",
        "purchase",
        "transport",
        "total",
    }

    assert set(result.costs) == expected_keys

    component_total = sum(
        result.costs[key]
        for key in expected_keys
        if key != "total"
    )

    assert result.costs["total"] == component_total
    assert result.costs["total"] > 0


def test_exponential_smoothing_differs_from_moving_average():
    """TC-SIM-08: Forecast method should affect forecast values."""
    config_ma = load_sample_config()
    config_es = copy.deepcopy(config_ma)

    config_ma["policy"]["forecast_method"] = "moving_average"
    config_es["policy"]["forecast_method"] = "exponential_smoothing"

    result_ma = run_simulation(config_ma)
    result_es = run_simulation(config_es)

    forecasts_ma = [
        record["forecast"]
        for record in result_ma.daily_records
    ]
    forecasts_es = [
        record["forecast"]
        for record in result_es.daily_records
    ]

    assert forecasts_ma != forecasts_es


def test_unreliable_suppliers_generate_delay_events():
    """TC-SIM-09: Suppliers with zero reliability should cause delays."""
    config = load_sample_config()

    for supplier in config["suppliers"]:
        supplier["reliability"] = 0.0

    result = run_simulation(config)

    delayed_events = [
        event
        for event in result.events
        if event["type"] == "PO_DELAYED"
    ]

    assert len(delayed_events) > 0


def test_simulation_returns_valid_kpis():
    """TC-SIM-10: Required KPIs should be returned with valid rates."""
    result = run_simulation(load_sample_config())

    expected_keys = {
        "fill_rate",
        "service_level",
        "avg_inventory_units",
        "inventory_turnover",
        "total_backorder_end",
        "forecast_mae",
    }

    assert expected_keys.issubset(result.kpis)

    assert 0 <= result.kpis["fill_rate"] <= 1
    assert 0 <= result.kpis["service_level"] <= 1

    assert result.kpis["avg_inventory_units"] >= 0
    assert result.kpis["inventory_turnover"] >= 0
    assert result.kpis["total_backorder_end"] >= 0
    assert result.kpis["forecast_mae"] >= 0


def test_unknown_forecast_method_raises_value_error():
    """Unknown forecast methods must not silently fall back."""
    config = load_sample_config()
    config["policy"]["forecast_method"] = "unknown_method"

    with pytest.raises(ValueError, match="Unknown forecast method"):
        run_simulation(config)
