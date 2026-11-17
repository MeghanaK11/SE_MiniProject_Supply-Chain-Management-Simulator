"""Tests for the logic behind the desktop window (SCM-F-036). No display needed."""
import json
from pathlib import Path

import pytest

from src import gui_model
from src.clock import EVENT_TYPES
from src.main import main

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = str(ROOT / "data" / "sample_config.json")
UNRELIABLE = str(ROOT / "data" / "scenarios" / "unreliable_suppliers.json")


def test_scenario_list_and_days_input():
    """TC-GUI-01: the scenario list starts with the sample config and holds every demo scenario; days input is blank or a whole number of at least 1."""
    scenarios = gui_model.list_scenarios(str(ROOT))
    assert scenarios[0] == gui_model.DEFAULT_CONFIG
    expected = sorted(p.name for p in (ROOT / "data" / "scenarios").glob("*.json"))
    assert [Path(p).name for p in scenarios[1:]] == expected
    assert gui_model.list_scenarios(str(ROOT / "tests")) == []
    assert gui_model.parse_days("") is None
    assert gui_model.parse_days("   ") is None
    assert gui_model.parse_days(None) is None
    assert gui_model.parse_days(" 45 ") == 45
    for bad in ("0", "-3", "2.5", "ten", "1e3"):
        with pytest.raises(ValueError, match="days"):
            gui_model.parse_days(bad)


def test_run_scenario_matches_cli(tmp_path):
    """TC-GUI-02: run_scenario gives the same records as the CLI, applies a day override, and rejects bad input with the CLI's errors."""
    result = gui_model.run_scenario(SAMPLE)
    assert len(result.daily_records) == 90
    cli_csv = tmp_path / "cli.csv"
    assert main(["--config", SAMPLE, "--out", str(cli_csv)]) == 0
    assert len(cli_csv.read_text(encoding="utf-8").splitlines()) == len(result.daily_records) + 1
    assert len(gui_model.run_scenario(SAMPLE, days=10).daily_records) == 30
    with pytest.raises(FileNotFoundError):
        gui_model.run_scenario(str(tmp_path / "missing.json"))
    with pytest.raises(ValueError, match="days"):
        gui_model.run_scenario(SAMPLE, days=5000)
    broken = tmp_path / "broken.json"
    broken.write_text('{"simulation":', encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        gui_model.run_scenario(str(broken))


def test_tables_show_kpis_costs_and_events():
    """TC-GUI-03: the KPI, cost and event tables show the run's values in the CLI's formats, and the event list filters by type."""
    result = gui_model.run_scenario(UNRELIABLE)
    kpis = dict(gui_model.kpi_rows(result.kpis))
    assert kpis["Fill rate"] == f"{result.kpis['fill_rate'] * 100:.2f}%"
    assert kpis["Service level"] == "93.33%"
    assert kpis["Backorder units at end"] == str(result.kpis["total_backorder_end"])
    assert kpis["Inventory turnover"] == f"{result.kpis['inventory_turnover']:.2f}"
    costs = dict(gui_model.cost_rows(result.costs))
    assert list(costs) == ["Holding", "Stockout", "Ordering", "Purchase", "Transport", "Total"]
    assert costs["Total"] == f"{result.costs['total']:,.2f}"
    counts = dict(gui_model.event_counts(result.events))
    assert list(counts) == list(EVENT_TYPES)
    assert counts["PO_DELAYED"] == 3
    assert len(gui_model.event_rows(result.events)) == sum(counts.values())
    delayed = gui_model.event_rows(result.events, "PO_DELAYED")
    assert len(delayed) == 3
    assert all(row[1] == "PO_DELAYED" and "delayed by" in row[2] for row in delayed)
    assert "unreliable_suppliers.json: 30 days, 3 products, 90 daily records" == gui_model.run_summary(UNRELIABLE, result)
    cards = {title: (text, level) for title, text, level in gui_model.summary_cards(result)}
    assert cards["Service level"] == ("93.33%", "warn")
    assert cards["Fill rate"] == (kpis["Fill rate"], "good")
    assert cards["Total cost (Rs)"] == ("510,653.10", "neutral")
    assert cards["Delayed orders"] == ("3", "warn")
    assert cards["Stockout events"][1] == ("good" if counts["STOCKOUT"] == 0 else "bad")
    for value, level in ((1.0, "good"), (0.98, "good"), (0.95, "warn"), (0.90, "warn"), (0.5, "bad")):
        assert gui_model.card_level("service_level", value) == level
    assert gui_model.card_level("PO_DELAYED", 0) == "good"
    assert gui_model.card_level("STOCKOUT", 2) == "bad"
    assert gui_model.card_level("STOCKOUT", 0) == "good"


def test_stock_series_and_chart_scaling():
    """TC-GUI-04: stock per product is ordered by day, and chart points map day 0 to the left margin, the last day to the right, 0 to the bottom and the highest stock to the top."""
    records = [
        {"day": 1, "product_id": "B", "stock_end": 5},
        {"day": 0, "product_id": "A", "stock_end": 10},
        {"day": 1, "product_id": "A", "stock_end": 0},
        {"day": 0, "product_id": "B", "stock_end": 20},
    ]
    series = gui_model.stock_series(records)
    assert series == {"A": [10, 0], "B": [20, 5]}
    points = gui_model.chart_points(series, width=200, height=100, margin=20)
    assert points["A"][0] == (20, 50.0)
    assert points["A"][1] == (180, 80)
    assert points["B"][0] == (20, 20)
    assert gui_model.chart_points({"A": [0]}, 200, 100, 20) == {"A": [(20, 80)]}
    assert gui_model.chart_points({}, 200, 100, 20) == {}
    with pytest.raises(ValueError, match="too small"):
        gui_model.chart_points(series, width=40, height=100, margin=20)
    full = gui_model.stock_series(gui_model.run_scenario(SAMPLE).daily_records)
    assert sorted(full) == ["P-001", "P-002", "P-003"]
    assert all(len(values) == 30 for values in full.values())
