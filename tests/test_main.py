import csv
import json
from pathlib import Path

from src.main import main

SAMPLE_CONFIG = Path(__file__).resolve().parent.parent / "data" / "sample_config.json"


def test_cli_success_returns_zero_and_writes_csv(tmp_path, capsys):
    """TC-SIM-05: a successful run returns 0, prints the summary and creates the output CSV."""
    out = tmp_path / "results" / "run.csv"
    assert main(["--days", "5", "--out", str(out)]) == 0
    assert out.is_file()
    with open(out, newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows[0][:3] == ["day", "product_id", "demand"]
    assert len(rows) == 1 + 5 * 3
    printed = capsys.readouterr().out
    assert "Fill rate" in printed
    assert str(out) in printed


def test_cli_missing_config_returns_two_with_one_error_line(tmp_path, capsys):
    """TC-SIM-06: a missing config file returns 2 and prints exactly one stderr line starting with Error:."""
    out = tmp_path / "never.csv"
    assert main(["--config", "missing.json", "--out", str(out)]) == 2
    captured = capsys.readouterr()
    lines = captured.err.strip().splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("Error:")
    assert not out.exists()


def test_cli_unknown_product_in_demand_returns_two_and_names_it(tmp_path, capsys):
    """TC-SIM-11: a demand section naming an unknown product returns 2 and stderr names it."""
    with open(SAMPLE_CONFIG, encoding="utf-8") as handle:
        config = json.load(handle)
    config["demand"]["P-999"] = {"pattern": "constant", "base": 1}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    out = tmp_path / "never.csv"
    assert main(["--config", str(config_path), "--out", str(out)]) == 2
    captured = capsys.readouterr()
    assert captured.err.startswith("Error:")
    assert "P-999" in captured.err
    assert not out.exists()