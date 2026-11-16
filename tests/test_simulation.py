import json
from pathlib import Path

import pytest

from src.clock import EventLog
from src.forecasting import exponential_smoothing
from src.simulation import SupplyChainSimulation


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def sample_config():
    """Load the sample configuration."""
    path = PROJECT_ROOT / "data" / "sample_config.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_scenario(filename):
    """Load a demo scenario configuration."""
    path = PROJECT_ROOT / "data" / "scenarios" / filename
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def run_sample(days=30, config=None):
    """Run the simulation using the supplied or sample configuration."""
    return SupplyChainSimulation(config or sample_config(), days).run()


# Original tests: TC-SIM-01 to TC-SIM-04

def test_thirty_days_gives_ninety_records():
    """TC-SIM-01: 30 days gives 90 daily records."""
    result = run_sample(30)
    assert len(result.daily_records) == 90
    assert isinstance(result.events, EventLog)


def test_stock_and_backorder_never_negative():
    """TC-SIM-02: Stock and backorder never become negative."""
    records = run_sample(30).daily_records
    assert all(
        r["stock_end"] >= 0 and r["backorder"] >= 0
        for r in records
    )
    assert sum(r["shipped"] for r in records) <= sum(
        r["demand"] for r in records
    )


def test_same_seed_gives_identical_records():
    """TC-SIM-03: Same seed gives identical daily records."""
    assert run_sample(30).daily_records == run_sample(30).daily_records


def test_low_starting_stock_triggers_purchase_order():
    """TC-SIM-04: Low P-003 stock triggers a purchase order."""
    placed = run_sample(30).events.events("PO_PLACED")
    assert any("P-003" in event["message"] for event in placed)


# New integration tests: TC-SIM-07 to TC-SIM-10

def test_demo_scenarios_run_successfully():
    """TC-SIM-07: Both v2 demo scenarios execute successfully."""
    for filename in (
        "exp_smoothing.json",
        "unreliable_suppliers.json",
    ):
        config = load_scenario(filename)
        result = SupplyChainSimulation(config).run()
        assert len(result.daily_records) > 0


def test_exponential_smoothing_forecast_is_used():
    """TC-SIM-08: Exponential smoothing policy uses the correct forecast."""
    config = load_scenario("exp_smoothing.json")
    simulation = SupplyChainSimulation(config)

    product_id = simulation.product_ids[0]
    alpha = config["policy"]["smoothing_alpha"]

    simulation._forecast(product_id, 10)
    actual_forecast = simulation._forecast(product_id, 20)

    expected_forecast = exponential_smoothing([10, 20], alpha)
    assert actual_forecast == pytest.approx(expected_forecast)


def test_unreliable_suppliers_generate_delay_events():
    """TC-SIM-09: Unreliable suppliers generate PO_DELAYED events."""
    config = load_scenario("unreliable_suppliers.json")

    # Make the delay behaviour deterministic for this test.
    for supplier in config["suppliers"]:
        supplier["reliability"] = 0.0

    result = SupplyChainSimulation(config).run()
    delayed_orders = result.events.events("PO_DELAYED")

    assert len(delayed_orders) > 0


def test_transport_cost_is_included_in_total_cost():
    """TC-SIM-10: Transport costs are included in total costs."""
    result = run_sample(30)
    costs = result.costs

    assert costs["transport"] > 0

    expected_total = sum(
        costs[key]
        for key in (
            "holding",
            "stockout",
            "ordering",
            "purchase",
            "transport",
        )
    )

    assert costs["total"] == pytest.approx(expected_total)
