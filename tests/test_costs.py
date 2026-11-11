
"""Tests for cost tracking (SCM-F-006)."""

import pytest

from src.costs import CostTracker
from src.products import Product


def sample_product():
    return Product(
        product_id="P-001",
        name="Test Product",
        unit_cost=100,
        holding_cost_per_day=0.50,
        stockout_penalty=30,
        order_cost=50,
    )


# --------------------------------------------------
# TC-CST-01: Holding cost
# --------------------------------------------------

def test_holding_cost():
    """TC-CST-01: Holding cost = 10 x 0.5 = 5.0."""
    tracker = CostTracker()
    product = sample_product()

    tracker.add_holding_cost(10, product)

    assert tracker.holding_cost == 5.0
    assert tracker.breakdown()["holding"] == 5.0


# --------------------------------------------------
# TC-CST-02: Stockout cost
# --------------------------------------------------

def test_stockout_cost():
    """TC-CST-02: Stockout cost = 3 x 30 = 90.0."""
    tracker = CostTracker()
    product = sample_product()

    tracker.add_stockout_cost(3, product)

    assert tracker.stockout_cost == 90.0
    assert tracker.breakdown()["stockout"] == 90.0


# --------------------------------------------------
# TC-CST-03: All cost types and total
# --------------------------------------------------

def test_all_cost_types_and_total():
    """TC-CST-03: Calculate each cost type and verify their total."""
    tracker = CostTracker()
    product = sample_product()

    tracker.add_holding_cost(10, product)
    tracker.add_stockout_cost(3, product)
    tracker.add_ordering_cost(product, 1)
    tracker.add_purchase_cost(2, 100)
    tracker.add_transport_cost(25.50)

    result = tracker.breakdown()

    assert result["holding"] == 5.0
    assert result["stockout"] == 90.0
    assert result["ordering"] == 50.0
    assert result["purchase"] == 200.0
    assert result["transport"] == 25.50

    expected_total = (
        result["holding"]
        + result["stockout"]
        + result["ordering"]
        + result["purchase"]
        + result["transport"]
    )

    assert result["total"] == expected_total
    assert result["total"] == 370.50
    assert tracker.total_cost == 370.50


def test_breakdown_rounds_values_to_two_decimals():
    """Verify breakdown values are rounded to two decimal places."""
    tracker = CostTracker()

    tracker.add_transport_cost(10.126)

    result = tracker.breakdown()

    assert result["transport"] == 10.13
    assert result["total"] == 10.13


# --------------------------------------------------
# TC-CST-04: Negative or invalid inputs
# --------------------------------------------------

@pytest.mark.parametrize(
    "operation",
    [
        "holding",
        "stockout",
        "ordering",
        "purchase_quantity",
        "purchase_price",
        "transport",
    ],
)
def test_negative_input_raises_value_error(operation):
    """TC-CST-04: Reject negative inputs across all cost methods."""
    tracker = CostTracker()
    product = sample_product()

    with pytest.raises(ValueError):
        if operation == "holding":
            tracker.add_holding_cost(-1, product)

        elif operation == "stockout":
            tracker.add_stockout_cost(-1, product)

        elif operation == "ordering":
            tracker.add_ordering_cost(product, -1)

        elif operation == "purchase_quantity":
            tracker.add_purchase_cost(-1, 100)

        elif operation == "purchase_price":
            tracker.add_purchase_cost(1, -100)

        elif operation == "transport":
            tracker.add_transport_cost(-10)


@pytest.mark.parametrize(
    "quantity",
    [1.5, True, "10", None],
)
def test_invalid_holding_quantity_raises_value_error(quantity):
    """TC-CST-04: Reject invalid holding quantities."""
    tracker = CostTracker()

    with pytest.raises(ValueError):
        tracker.add_holding_cost(quantity, sample_product())


def test_invalid_transport_amount_raises_value_error():
    """TC-CST-04: Reject non-finite transport amounts."""
    tracker = CostTracker()

    with pytest.raises(ValueError):
        tracker.add_transport_cost(float("inf"))

    with pytest.raises(ValueError):
        tracker.add_transport_cost(float("nan"))
