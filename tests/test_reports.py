import csv

import pytest

from src.reports import export_daily_csv, format_summary

KPIS = {"fill_rate": 0.9, "service_level": 0.95, "avg_inventory_units": 12.5,
        "inventory_turnover": 3.0, "total_backorder_end": 4, "forecast_mae": 1.2345}
COSTS = {"holding": 5.0, "stockout": 90.0, "ordering": 500.0, "purchase": 1000.0,
         "transport": 0.0, "total": 1595.0}


def record(**overrides):
    fields = {"day": 0, "product_id": "P-001", "demand": 10, "shipped": 8, "stock_end": 20,
              "backorder": 2, "on_order": 0, "forecast": 9.5}
    fields.update(overrides)
    return fields


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.reader(handle))


def test_csv_has_header_and_one_row_per_record(tmp_path):
    """TC-RPT-01: the CSV has the eight columns in order and one row per product-day."""
    path = tmp_path / "out.csv"
    export_daily_csv([record(day=0), record(day=1, product_id="P-002")], str(path))
    rows = read_rows(path)
    assert rows[0] == ["day", "product_id", "demand", "shipped", "stock_end",
                       "backorder", "on_order", "forecast"]
    assert len(rows) == 3
    assert rows[1][:2] == ["0", "P-001"]


def test_csv_creates_parent_folders_and_rejects_incomplete_record(tmp_path):
    """TC-RPT-02: parent folders are created, and a record missing a column raises ValueError."""
    path = tmp_path / "a" / "b" / "out.csv"
    export_daily_csv([record()], str(path))
    assert path.is_file()
    bad = record()
    del bad["forecast"]
    with pytest.raises(ValueError, match="forecast"):
        export_daily_csv([bad], str(tmp_path / "bad.csv"))


def test_formula_text_is_neutralised_and_numbers_unchanged(tmp_path):
    """TC-RPT-03: a product ID of =HYPERLINK(1) is written with a leading apostrophe; numbers are unchanged."""
    path = tmp_path / "out.csv"
    export_daily_csv([record(product_id="=HYPERLINK(1)", stock_end=20)], str(path))
    row = read_rows(path)[1]
    assert row[1] == "'=HYPERLINK(1)"
    assert row[4] == "20"


def test_all_formula_prefixes_are_neutralised(tmp_path):
    """TC-RPT-04: text starting with =, +, - or @ gets an apostrophe; ordinary text does not."""
    path = tmp_path / "out.csv"
    ids = ["=A1", "+A1", "-A1", "@A1", "P-001"]
    export_daily_csv([record(product_id=pid) for pid in ids], str(path))
    cells = [row[1] for row in read_rows(path)[1:]]
    assert cells == ["'=A1", "'+A1", "'-A1", "'@A1", "P-001"]


def test_summary_shows_costs_and_percentages():
    """TC-RPT-05: the summary shows 'Fill rate: 90.00%' for 0.9 and costs with two decimals."""
    text = format_summary(KPIS, COSTS)
    assert "Fill rate: 90.00%" in text
    assert "Service level: 95.00%" in text
    assert "Total cost: 1595.00" in text
    assert "Mean absolute error: 1.23" in text
    with pytest.raises(ValueError, match="fill_rate"):
        format_summary({}, COSTS)