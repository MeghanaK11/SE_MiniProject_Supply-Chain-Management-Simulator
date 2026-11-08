import pytest

from src.inventory import Warehouse


def test_TC_INV_01_receive_increases_stock():
    """Receiving stock should increase the product's stock level."""
    warehouse = Warehouse("W1", "Main Warehouse")

    updated_stock = warehouse.receive("P1", 10)

    assert updated_stock == 10
    assert warehouse.stock_level("P1") == 10


def test_TC_INV_02_ship_requested_quantity():
    """Shipping fewer units than available should ship the full request."""
    warehouse = Warehouse(
        "W1",
        "Main Warehouse",
        {"P1": 10},
    )

    shipped = warehouse.ship("P1", 4)

    assert shipped == 4
    assert warehouse.stock_level("P1") == 6


def test_TC_INV_03_ship_partial_stock():
    """Shipping more than available should ship only available stock."""
    warehouse = Warehouse(
        "W1",
        "Main Warehouse",
        {"P1": 5},
    )

    shipped = warehouse.ship("P1", 8)

    assert shipped == 5
    assert warehouse.stock_level("P1") == 0


@pytest.mark.parametrize(
    "invalid_quantity",
    [0, -2, 2.5, True, "5"],
)
def test_TC_INV_04_reject_invalid_quantities(invalid_quantity):
    """Receive and ship must reject zero, negative and non-integer quantities."""
    warehouse = Warehouse(
        "W1",
        "Main Warehouse",
        {"P1": 10},
    )

    with pytest.raises(ValueError):
        warehouse.receive("P1", invalid_quantity)

    with pytest.raises(ValueError):
        warehouse.ship("P1", invalid_quantity)


@pytest.mark.parametrize(
    "invalid_initial_stock",
    [
        {"P1": -1},
        {"P1": 2.5},
        {"P1": True},
        {"P1": "5"},
    ],
)
def test_TC_INV_04_reject_invalid_initial_stock(invalid_initial_stock):
    """Initial stock must contain only non-negative integer quantities."""
    with pytest.raises(ValueError):
        Warehouse("W1", "Main Warehouse", invalid_initial_stock)


def test_TC_INV_05_unknown_product_has_zero_stock():
    """An unknown product should have zero stock."""
    warehouse = Warehouse(
        "W1",
        "Main Warehouse",
        {"P1": 10},
    )

    assert warehouse.stock_level("UNKNOWN") == 0


def test_TC_INV_06_snapshot_returns_a_copy():
    """Changing a snapshot must not change the warehouse's actual stock."""
    warehouse = Warehouse(
        "W1",
        "Main Warehouse",
        {"P1": 10},
    )

    stock_snapshot = warehouse.snapshot()
    stock_snapshot["P1"] = 100

    assert warehouse.stock_level("P1") == 10
    assert stock_snapshot["P1"] == 100