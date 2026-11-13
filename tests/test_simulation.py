import json

from src.clock import EventLog
from src.simulation import SupplyChainSimulation


def sample_config():
    with open("data/sample_config.json", encoding="utf-8") as handle:
        return json.load(handle)


def run_sample(days=30, config=None):
    return SupplyChainSimulation(config or sample_config(), days).run()


def test_thirty_days_gives_ninety_records():
    """TC-SIM-01: 30 days on the sample config gives 90 daily records (30 days x 3 products)."""
    result = run_sample(30)
    assert len(result.daily_records) == 90
    assert isinstance(result.events, EventLog)


def test_stock_and_backorder_never_negative():
    """TC-SIM-02: stock_end and backorder are never negative, and total shipped never exceeds total demand."""
    records = run_sample(30).daily_records
    assert all(r["stock_end"] >= 0 and r["backorder"] >= 0 for r in records)
    assert sum(r["shipped"] for r in records) <= sum(r["demand"] for r in records)


def test_same_seed_gives_identical_records():
    """TC-SIM-03: running twice with the same seed gives identical daily_records."""
    assert run_sample(30).daily_records == run_sample(30).daily_records


def test_low_starting_stock_triggers_purchase_order():
    """TC-SIM-04: P-003 starts low, so at least one PO_PLACED event mentions P-003."""
    placed = run_sample(30).events.events("PO_PLACED")
    assert any("P-003" in event["message"] for event in placed)