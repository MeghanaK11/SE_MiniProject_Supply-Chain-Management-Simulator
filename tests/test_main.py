import csv

from src.main import main


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