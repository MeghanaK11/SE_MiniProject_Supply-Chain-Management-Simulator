
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


# ============================================================
# TC-KPI-01: Fill rate
# ============================================================

def test_fill_rate():
    """TC-KPI-01: Calculate fill rate correctly."""
    assert fill_rate(180, 200) == 0.9


@pytest.mark.parametrize(
    "shipped,demand",
    [
        (-1, 10),
        (1, -10),
        (True, 10),
        (10, True),
        ("5", 10),
        (5, float("inf")),
        (5, float("nan")),
    ],
)
def test_fill_rate_rejects_invalid_inputs(shipped, demand):
    """TC-KPI-01: Reject invalid fill-rate inputs."""
    with pytest.raises(ValueError):
        fill_rate(shipped, demand)


def test_fill_rate_rejects_shipped_greater_than_demand():
    """TC-KPI-01: Reject aggregate shipments exceeding aggregate demand."""
    with pytest.raises(ValueError, match="cannot exceed"):
        fill_rate(11, 10)


# ============================================================
# TC-KPI-02: Service level
# ============================================================

def test_service_level():
    """TC-KPI-02: Calculate service level correctly."""
    records = sample_records()
    assert service_level(records) == 0.5


def test_service_level_empty_records():
    """TC-KPI-02: Return zero service level for empty records."""
    assert service_level([]) == 0.0


# ============================================================
# TC-KPI-03: Inventory turnover
# ============================================================

def test_inventory_turnover_uses_distinct_days():
    """TC-KPI-03: Calculate average inventory using distinct days."""
    products = [
        Product(
            product_id=f"P-00{i}",
            name=f"Product {i}",
            unit_cost=10,
            holding_cost_per_day=0.5,
            stockout_penalty=30,
            order_cost=50,
        )
        for i in range(1, 4)
    ]

    records = []
    for day in range(2):
        for product in products:
            records.append(
                {
                    "day": day,
                    "product_id": product.product_id,
                    "demand": 10,
                    "shipped": 5,
                    "stock_end": 10,
                    "backorder": 0,
                    "on_order": 0,
                    "forecast": 10.0,
                }
            )

    # COGS = 6 rows * 5 shipped * 10 unit cost = 300.
    # Inventory value = 6 rows * 10 stock * 10 unit cost = 600.
    # Average inventory value = 600 / 2 distinct days = 300.
    assert inventory_turnover(records, products) == 1.0


def test_inventory_turnover_zero_average_inventory():
    """TC-KPI-03: Return zero when average inventory value is zero."""
    records = sample_records()
    for record in records:
        record["stock_end"] = 0

    assert inventory_turnover(records, sample_products()) == 0.0


def test_inventory_turnover_empty_records():
    """TC-KPI-03: Return zero for empty records."""
    assert inventory_turnover([], sample_products()) == 0.0


def test_inventory_turnover_unknown_product():
    """TC-KPI-03: Reject unknown products."""
    records = sample_records()
    records[0]["product_id"] = "P-999"

    with pytest.raises(ValueError, match="unknown product_id"):
        inventory_turnover(records, sample_products())


# ============================================================
# TC-KPI-04: Invalid inputs and validation
# ============================================================

def test_invalid_records_rejected_for_wrong_container():
    """TC-KPI-04: Reject unsupported daily-record containers."""
    with pytest.raises(ValueError, match="list or tuple"):
        compute_kpis("not records", sample_products())


def test_invalid_record_type_rejected():
    """TC-KPI-04: Reject invalid record types."""
    with pytest.raises(ValueError, match="must be a dictionary"):
        compute_kpis([None], sample_products())


def test_missing_record_field_rejected():
    """TC-KPI-04: Reject records with missing required fields."""
    with pytest.raises(ValueError, match="missing required field"):
        compute_kpis([{"product_id": "P-001"}], sample_products())


@pytest.mark.parametrize(
    "field,value",
    [
        ("day", -1),
        ("day", True),
        ("demand", -1),
        ("demand", 1.5),
        ("shipped", -1),
        ("shipped", True),
        ("stock_end", -1),
        ("stock_end", 1.5),
        ("backorder", -1),
        ("backorder", True),
        ("on_order", -1),
        ("on_order", 1.5),
    ],
)
def test_record_rejects_invalid_integer_fields(field, value):
    """TC-KPI-04: Reject invalid integer fields."""
    records = sample_records()
    records[0][field] = value

    with pytest.raises(ValueError, match=field):
        compute_kpis(records, sample_products())


@pytest.mark.parametrize(
    "product_id",
    ["", "   ", None, 123, True],
)
def test_record_rejects_invalid_product_id(product_id):
    """TC-KPI-04: Reject invalid product IDs."""
    records = sample_records()
    records[0]["product_id"] = product_id

    with pytest.raises(ValueError, match="product_id"):
        compute_kpis(records, sample_products())


@pytest.mark.parametrize(
    "forecast",
    [-1, True, "100", None, float("nan"), float("inf")],
)
def test_record_rejects_invalid_forecast(forecast):
    """TC-KPI-04: Reject invalid forecast values."""
    records = sample_records()
    records[0]["forecast"] = forecast

    with pytest.raises(ValueError, match="forecast"):
        compute_kpis(records, sample_products())


@pytest.mark.parametrize(
    "forecast_mae",
    [-1, True, "5", None, float("nan"), float("inf")],
)
def test_invalid_forecast_mae_rejected(forecast_mae):
    """TC-KPI-04: Reject invalid forecast MAE values."""
    with pytest.raises(ValueError, match="forecast_mae"):
        compute_kpis(
            sample_records(),
            sample_products(),
            forecast_mae=forecast_mae,
        )


def test_products_must_be_supported_collection():
    """TC-KPI-04: Reject unsupported product collections."""
    with pytest.raises(ValueError, match="products must be"):
        inventory_turnover(sample_records(), "invalid products")


def test_product_without_unit_cost_rejected():
    """TC-KPI-04: Reject products without unit cost."""

    class ProductWithoutCost:
        product_id = "P-001"

    with pytest.raises(ValueError, match="unit_cost"):
        inventory_turnover(sample_records(), [ProductWithoutCost()])


@pytest.mark.parametrize(
    "cost",
    [-1, True, "10", None, float("nan"), float("inf")],
)
def test_invalid_product_unit_cost_rejected(cost):
    """TC-KPI-04: Reject invalid product unit costs."""

    class ProductWithInvalidCost:
        product_id = "P-001"
        unit_cost = cost

    with pytest.raises(ValueError, match="invalid unit_cost"):
        inventory_turnover(
            sample_records(),
            [ProductWithInvalidCost()],
        )


# ============================================================
# TC-KPI-05: Average inventory and overall KPIs
# ============================================================

def test_average_inventory_units():
    """TC-KPI-05: Calculate average inventory units correctly."""
    records = sample_records()
    assert average_inventory_units(records) == 40.0


def test_average_inventory_units_empty_records():
    """TC-KPI-05: Return zero average inventory for empty records."""
    assert average_inventory_units([]) == 0.0


def test_zero_demand_returns_full_fill_rate():
    """TC-KPI-05: Return fill rate of 1.0 when demand is zero."""
    assert fill_rate(0, 0) == 1.0


def test_empty_records_return_zero_kpis():
    """TC-KPI-05: Return default KPIs for an empty simulation."""
    result = compute_kpis([], sample_products())

    assert result["fill_rate"] == 1.0
    assert result["service_level"] == 0.0
    assert result["avg_inventory_units"] == 0.0
    assert result["inventory_turnover"] == 0.0
    assert result["total_backorder_end"] == 0
    assert result["forecast_mae"] == 0.0


def test_unknown_product_rejected():
    """TC-KPI-05: Reject unknown products during KPI calculation."""
    records = sample_records()
    records[0]["product_id"] = "P-999"

    with pytest.raises(ValueError, match="unknown product_id"):
        compute_kpis(records, sample_products())


def test_compute_kpis():
    """TC-KPI-05: Calculate all KPIs correctly."""
    result = compute_kpis(
        sample_records(),
        sample_products(),
        forecast_mae=5.123456,
    )

    assert result["fill_rate"] == 0.9
    assert result["service_level"] == 0.5
    assert result["avg_inventory_units"] == 40.0
    assert result["inventory_turnover"] == 4.5
    assert result["total_backorder_end"] == 0
    assert result["forecast_mae"] == 5.1235


def test_kpi_values_are_rounded_to_four_decimals():
    """TC-KPI-05: Round KPI values to four decimal places."""
    records = sample_records()
    records[0]["demand"] = 3
    records[0]["shipped"] = 1
    records[1]["demand"] = 3
    records[1]["shipped"] = 1

    result = compute_kpis(
        records,
        sample_products(),
        forecast_mae=1.234567,
    )

    assert result["fill_rate"] == 0.3333
    assert result["forecast_mae"] == 1.2346


def test_inventory_turnover_accepts_product_catalog_like_object():
    """TC-KPI-05: Support product catalog objects."""

    class ProductCollection:
        def list_all(self):
            return sample_products()

    assert inventory_turnover(
        sample_records(),
        ProductCollection(),
    ) == 4.5


def test_inventory_turnover_accepts_product_dictionary():
    """TC-KPI-05: Support product dictionaries."""
    products = {
        "P-001": sample_products()[0]
    }

    assert inventory_turnover(
        sample_records(),
        products,
    ) == 4.5
