"""System validation tests ST-01 to ST-08 (B-33).

Black-box tests that run the product through main(argv) like a user would,
using config files written to tmp_path from data/sample_config.json with one
thing changed. ST-05 and ST-06 read the event log, which the command line does
not print, so they use the engine on the same kind of config.
"""
import copy
import csv
import json
from pathlib import Path

import pytest

from src.config_loader import load_config
from src.main import main
from src.simulation import SupplyChainSimulation

SAMPLE_CONFIG = Path(__file__).resolve().parent.parent / "data" / "sample_config.json"


def sample_config() -> dict:
    with open(SAMPLE_CONFIG, encoding="utf-8") as handle:
        return json.load(handle)


def write_config(tmp_path, config: dict, name: str = "config.json") -> str:
    path = tmp_path / name
    path.write_text(json.dumps(config), encoding="utf-8")
    return str(path)


def read_csv(path) -> list:
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.system
def test_st01_run_simulation_writes_csv_and_summary(tmp_path, capsys):
    """ST-01 (UC-1; F-034, F-035): a 30-day run returns 0, writes header plus 90 rows and prints Fill rate."""
    out = tmp_path / "results.csv"
    assert main(["--days", "30", "--out", str(out)]) == 0
    with open(out, newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert len(rows) == 1 + 90
    assert "Fill rate" in capsys.readouterr().out


@pytest.mark.system
def test_st02_missing_config_is_one_error_line(tmp_path, capsys):
    """ST-02 (NF-004; F-031): a missing config file returns 2 and stderr starts with Error:."""
    assert main(["--config", str(tmp_path / "missing.json"), "--out", str(tmp_path / "x.csv")]) == 2
    assert capsys.readouterr().err.startswith("Error:")


@pytest.mark.system
def test_st03_unknown_product_in_demand_is_rejected(tmp_path, capsys):
    """ST-03 (SR-001): a demand section naming P-999 returns 2 and the message mentions P-999."""
    config = sample_config()
    config["demand"]["P-999"] = {"pattern": "constant", "base": 1}
    path = write_config(tmp_path, config)
    assert main(["--config", path, "--out", str(tmp_path / "x.csv")]) == 2
    assert "P-999" in capsys.readouterr().err


@pytest.mark.system
def test_st04_days_above_limit_is_rejected(tmp_path, capsys):
    """ST-04 (SR-002): --days 5000 returns 2."""
    assert main(["--days", "5000", "--out", str(tmp_path / "x.csv")]) == 2
    assert capsys.readouterr().err.startswith("Error:")


@pytest.mark.system
def test_st05_purchase_order_is_placed_received_and_stock_rises():
    """ST-05 (UC-1; F-005, F-014): P-003 gets a PO_PLACED and a later PO_RECEIVED, and stock_end rises after the receipt."""
    result = SupplyChainSimulation(load_config(str(SAMPLE_CONFIG)), days=30).run()
    placed = [e for e in result.events.events("PO_PLACED") if "P-003" in e["message"]]
    received = [e for e in result.events.events("PO_RECEIVED") if "P-003" in e["message"]]
    assert placed and received
    assert received[0]["day"] > placed[0]["day"]
    stock = {r["day"]: r["stock_end"] for r in result.daily_records if r["product_id"] == "P-003"}
    day = received[0]["day"]
    assert stock[day] > stock[day - 1]


@pytest.mark.system
def test_st06_unreliable_suppliers_cause_delays():
    """ST-06 (UC-2; F-015): with every reliability at 0.0 there is at least one PO_DELAYED event."""
    config = sample_config()
    for supplier in config["suppliers"]:
        supplier["reliability"] = 0.0
    result = SupplyChainSimulation(config, days=30).run()
    assert result.events.count("PO_DELAYED") >= 1


@pytest.mark.system
def test_st07_forecast_method_changes_forecast_column(tmp_path):
    """ST-07 (UC-2; F-025): the same seed with moving_average versus exponential_smoothing gives different forecast columns."""
    forecasts = {}
    for method in ("moving_average", "exponential_smoothing"):
        config = copy.deepcopy(sample_config())
        config["policy"]["forecast_method"] = method
        path = write_config(tmp_path, config, f"{method}.json")
        out = tmp_path / f"{method}.csv"
        assert main(["--config", path, "--days", "30", "--out", str(out)]) == 0
        forecasts[method] = [row["forecast"] for row in read_csv(out)]
    assert forecasts["moving_average"] != forecasts["exponential_smoothing"]


@pytest.mark.system
def test_st08_formula_product_id_is_neutralised_in_csv(tmp_path):
    """ST-08 (SR-003): a product_id starting with = is written to the CSV with a leading apostrophe."""
    text = json.dumps(sample_config()).replace("P-001", "=P-001")
    path = tmp_path / "config.json"
    path.write_text(text, encoding="utf-8")
    out = tmp_path / "results.csv"
    assert main(["--config", str(path), "--days", "5", "--out", str(out)]) == 0
    cells = {row["product_id"] for row in read_csv(out)}
    assert "'=P-001" in cells
    assert "=P-001" not in cells