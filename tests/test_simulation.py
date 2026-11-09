
"""Tests for Simulation Engine v2."""

import copy
import json
from pathlib import Path

from src.simulation import run_simulation


CONFIG_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_config.json"


def load_sample_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


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
        event for event in result.events
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
