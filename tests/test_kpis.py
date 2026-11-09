
"""Tests for KPI calculations (SCM-F-033)."""

import pytest

from src.kpis import (
    fill_rate,
    service_level,
    average_inventory_units,
    inventory_turnover,
    compute_kpis,
)
from src.products import Product


def sample_products():
    return [
        Product(
            product_id="P-001",
            name="Product One",
            unit_cost=10,
            holding_cost_per_day=0.5,
            stockout_penalty=30,
            order_cost=50,
        )
    ]


def sample_records():
    return [
        {
            "day": 0,
            "product_id": "P-001",
            "demand": 100,
            "shipped": 90,
            "stock_end": 50,
            "backorder": 10,
            "on_order": 20,
            "forecast": 100.0,
        },
        {
            "day": 1,
            "product_id": "P-001",
            "demand": 100,
            "shipped": 90,
            "stock_end": 30,
            "backorder": 0,
            "on_order": 10,
            "forecast": 100.0,
        },
    ]


def test_fill_rate():
    """TC-KPI-01: Calculate fill rate correctly."""
    assert fill_rate(180, 200) == pytest.approx(0.90)


def test_service_level():
    """TC-KPI-02: Calculate service level using product-days."""
    records = sample_records()
    assert service_level(records) == pytest.approx(0.50)


def test_average_inventory_units():
    """TC-KPI-03: Calculate average inventory."""
    records = sample_records()
    assert average_inventory_units(records) == pytest.approx(40.0)


def test_inventory_turnover():
    """TC-KPI-04: Calculate inventory turnover."""
    records = sample_records()
    products = sample_products()

    # COGS = 180 * 10 = 1800
    # Average inventory value = ((50 * 10) + (30 * 10)) / 2 = 400
    assert inventory_turnover(records, products) == pytest.approx(4.5)


def test_compute_kpis():
    """TC-KPI-05: Calculate all KPIs together."""
    result = compute_kpis(
        sample_records(),
        sample_products(),
        forecast_mae=5.0,
    )

    assert result["fill_rate"] == pytest.approx(0.90)
    assert result["service_level"] == pytest.approx(0.50)
    assert result["avg_inventory_units"] == pytest.approx(40.0)
    assert result["inventory_turnover"] == pytest.approx(4.5)
    assert result["total_backorder_end"] == 0
    assert result["forecast_mae"] == pytest.approx(5.0)


def test_zero_demand_returns_zero_fill_rate():
    assert fill_rate(0, 0) == 0.0


def test_empty_records_return_zero_kpis():
    result = compute_kpis([], sample_products())

    assert result["fill_rate"] == 0.0
    assert result["service_level"] == 0.0
    assert result["avg_inventory_units"] == 0.0
    assert result["inventory_turnover"] == 0.0
    assert result["total_backorder_end"] == 0


def test_invalid_records_rejected():
    with pytest.raises(ValueError):
        compute_kpis([{"product_id": "P-001"}], sample_products())


def test_unknown_product_rejected():
    records = sample_records()
    records[0]["product_id"] = "P-999"

    with pytest.raises(ValueError, match="unknown product_id"):
        compute_kpis(records, sample_products())
