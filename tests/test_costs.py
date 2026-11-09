
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


def test_holding_and_stockout_cost():
    """TC-CST-01: Calculate holding and stockout costs."""
    tracker = CostTracker()
    product = sample_product()

    tracker.add_holding_cost(10, product)
    tracker.add_stockout_cost(3, product)

    assert tracker.holding_cost == 5.0
    assert tracker.stockout_cost == 90.0


def test_ordering_and_purchase_cost():
    """TC-CST-02: Calculate ordering and purchase costs."""
    tracker = CostTracker()
    product = sample_product()

    tracker.add_ordering_cost(product, 2)
    tracker.add_purchase_cost(10, 100)

    assert tracker.ordering_cost == 100.0
    assert tracker.purchase_cost == 1000.0


def test_transport_cost_accumulation():
    """TC-CST-03: Accumulate transport costs."""
    tracker = CostTracker()

    tracker.add_transport_cost(125.50)
    tracker.add_transport_cost(74.50)

    assert tracker.transport_cost == 200.0


def test_total_and_cost_breakdown():
    """TC-CST-04: Total equals the sum of all cost categories."""
    tracker = CostTracker()
    product = sample_product()

    tracker.add_holding_cost(10, product)
    tracker.add_stockout_cost(3, product)
    tracker.add_ordering_cost(product, 2)
    tracker.add_purchase_cost(10, 100)
    tracker.add_transport_cost(200)

    result = tracker.breakdown()

    assert result["holding"] == 5.0
    assert result["stockout"] == 90.0
    assert result["ordering"] == 100.0
    assert result["purchase"] == 1000.0
    assert result["transport"] == 200.0
    assert result["total"] == 1395.0
    assert tracker.total_cost == 1395.0


@pytest.mark.parametrize("quantity", [-1, 1.5, True])
def test_invalid_holding_quantity(quantity):
    """Reject invalid inventory quantities."""
    tracker = CostTracker()

    with pytest.raises(ValueError):
        tracker.add_holding_cost(quantity, sample_product())


def test_negative_transport_cost_rejected():
    """Reject negative transport costs."""
    tracker = CostTracker()

    with pytest.raises(ValueError):
        tracker.add_transport_cost(-10)
