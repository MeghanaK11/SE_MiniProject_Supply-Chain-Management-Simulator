import pytest

from src.inventory import Warehouse


def test_initial_stock():
    """TC-INV-01: Warehouse starts with the given stock."""
    warehouse = Warehouse("W1", "Main Warehouse", {"P-001": 10})

    assert warehouse.stock_level("P-001") == 10


def test_receive_stock():
    """TC-INV-02: Receiving stock increases inventory."""
    warehouse = Warehouse("W1", "Main Warehouse", {"P-001": 10})

    warehouse.receive("P-001", 5)

    assert warehouse.stock_level("P-001") == 15


def test_ship_stock():
    """TC-INV-03: Shipping cannot exceed available stock."""
    warehouse = Warehouse("W1", "Main Warehouse", {"P-001": 5})

    shipped = warehouse.ship("P-001", 8)

    assert shipped == 5
    assert warehouse.stock_level("P-001") == 0


def test_stock_level_for_unknown_product():
    """TC-INV-04: Unknown products have zero stock."""
    warehouse = Warehouse("W1", "Main Warehouse", {})

    assert warehouse.stock_level("P-999") == 0


def test_invalid_quantities():
    """TC-INV-05: Zero and negative quantities are rejected."""
    warehouse = Warehouse("W1", "Main Warehouse", {})

    with pytest.raises(ValueError):
        warehouse.receive("P-001", 0)

    with pytest.raises(ValueError):
        warehouse.ship("P-001", -2)


def test_snapshot():
    """TC-INV-06: Snapshot returns a separate copy of stock."""
    warehouse = Warehouse("W1", "Main Warehouse", {"P-001": 10})

    stock_snapshot = warehouse.snapshot()
    stock_snapshot["P-001"] = 100

    assert warehouse.stock_level("P-001") == 10