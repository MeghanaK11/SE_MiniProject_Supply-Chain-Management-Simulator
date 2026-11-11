import pytest

from src.inventory import (
    Warehouse,
    safety_stock,
    reorder_point,
)


# B-07: Warehouse stock tests (TC-INV-01 to TC-INV-06)


def test_warehouse_initial_stock():
    """TC-INV-01: Warehouse stores initial stock correctly."""
    warehouse = Warehouse("W1", "Main Warehouse", {"P1": 100})

    assert warehouse.stock_level("P1") == 100


def test_receive_stock():
    """TC-INV-02: Receiving stock increases inventory."""
    warehouse = Warehouse("W1", "Main Warehouse", {"P1": 100})

    warehouse.receive("P1", 50)

    assert warehouse.stock_level("P1") == 150


def test_ship_stock():
    """TC-INV-03: Shipping stock decreases inventory."""
    warehouse = Warehouse("W1", "Main Warehouse", {"P1": 100})

    shipped = warehouse.ship("P1", 30)

    assert shipped == 30
    assert warehouse.stock_level("P1") == 70


def test_ship_never_causes_negative_stock():
    """TC-INV-04: Shipping cannot reduce stock below zero."""
    warehouse = Warehouse("W1", "Main Warehouse", {"P1": 10})

    shipped = warehouse.ship("P1", 20)

    assert shipped == 10
    assert warehouse.stock_level("P1") == 0


def test_snapshot_returns_copy():
    """TC-INV-05: Snapshot returns a copy of warehouse inventory."""
    warehouse = Warehouse("W1", "Main Warehouse", {"P1": 100})

    result = warehouse.snapshot()
    result["P1"] = 999

    assert warehouse.stock_level("P1") == 100


def test_invalid_stock_quantities():
    """TC-INV-06: Invalid stock quantities are rejected."""
    warehouse = Warehouse("W1", "Main Warehouse", {"P1": 10})

    with pytest.raises(ValueError):
        warehouse.receive("P1", 0)

    with pytest.raises(ValueError):
        warehouse.ship("P1", -5)

    with pytest.raises(ValueError):
        Warehouse("W1", "Main Warehouse", {"P1": -10})


# B-16: Safety stock and reorder point tests (TC-INV-11 to TC-INV-15)


def test_safety_stock_calculation():
    """TC-INV-11: Safety stock follows the specified formula."""
    result = safety_stock(
        z=1.65,
        demand_std_per_day=4,
        lead_time_days=9
    )

    assert result == 20


def test_safety_stock_zero_variability():
    """TC-INV-12: Zero demand variability produces zero safety stock."""
    assert safety_stock(1.65, 0, 9) == 0


def test_reorder_point_calculation():
    """TC-INV-13: Reorder point follows the specified formula."""
    assert reorder_point(10, 5, 20) == 70


def test_reorder_point_rounds_up():
    """TC-INV-14: Reorder point rounds fractional values upwards."""
    assert reorder_point(4.5, 3, 2) == 16


def test_warehouse_reorder_decision():
    """TC-INV-15: Reorder is triggered when stock plus open orders is at or below ROP."""
    warehouse = Warehouse("W1", "Main Warehouse", {"P1": 20})

    # Stock 20 + open orders 5 = 25, which is below ROP 30.
    assert warehouse.needs_reorder("P1", 30, 5) is True

    # Stock 20 + open orders 10 = 30, exactly at ROP.
    assert warehouse.needs_reorder("P1", 30, 10) is True

    # Stock 20 + open orders 11 = 31, above ROP.
    assert warehouse.needs_reorder("P1", 30, 11) is False


def test_negative_reorder_inputs_rejected():
    """Negative reorder inputs must be rejected."""
    warehouse = Warehouse("W1", "Main Warehouse", {"P1": 20})

    with pytest.raises(ValueError):
        safety_stock(-1, 4, 9)

    with pytest.raises(ValueError):
        reorder_point(10, -1, 20)

    with pytest.raises(ValueError):
        warehouse.needs_reorder("P1", -1, 5)

    with pytest.raises(ValueError):
        warehouse.needs_reorder("P1", 30, -5)