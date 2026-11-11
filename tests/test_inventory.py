
import json
from pathlib import Path

import pytest

from src.inventory import (
    Warehouse,
    economic_order_quantity,
    safety_stock,
    reorder_point,
)


# ============================================================
# B-07: Warehouse Stock Management
# Test Cases: TC-INV-01 to TC-INV-06
# ============================================================

def test_warehouse_initial_stock():
    warehouse = Warehouse(
        "W-001",
        "Main Warehouse",
        {"P-001": 100, "P-002": 50},
    )

    assert warehouse.stock_level("P-001") == 100
    assert warehouse.stock_level("P-002") == 50
    assert warehouse.stock_level("P-003") == 0


def test_warehouse_receive_stock():
    warehouse = Warehouse("W-001", "Main Warehouse", {"P-001": 100})

    warehouse.receive("P-001", 25)

    assert warehouse.stock_level("P-001") == 125


def test_warehouse_ship_stock():
    warehouse = Warehouse("W-001", "Main Warehouse", {"P-001": 100})

    shipped = warehouse.ship("P-001", 30)

    assert shipped == 30
    assert warehouse.stock_level("P-001") == 70


def test_warehouse_cannot_have_negative_stock():
    warehouse = Warehouse("W-001", "Main Warehouse", {"P-001": 10})

    shipped = warehouse.ship("P-001", 20)

    assert shipped == 10
    assert warehouse.stock_level("P-001") == 0


def test_warehouse_snapshot_returns_copy():
    warehouse = Warehouse("W-001", "Main Warehouse", {"P-001": 100})

    snapshot = warehouse.snapshot()
    snapshot["P-001"] = 500

    assert warehouse.stock_level("P-001") == 100


@pytest.mark.parametrize(
    "invalid_stock",
    [
        None,
        [],
        "100",
    ],
)
def test_invalid_initial_stock_type(invalid_stock):
    with pytest.raises(ValueError):
        Warehouse("W-001", "Main Warehouse", invalid_stock)


@pytest.mark.parametrize(
    "invalid_quantity",
    [
        -1,
        1.5,
        True,
        "10",
        None,
    ],
)
def test_invalid_initial_stock_quantity(invalid_quantity):
    with pytest.raises(ValueError):
        Warehouse(
            "W-001",
            "Main Warehouse",
            {"P-001": invalid_quantity},
        )


@pytest.mark.parametrize(
    "invalid_quantity",
    [
        0,
        -5,
        1.5,
        True,
        "10",
        None,
    ],
)
def test_receive_rejects_invalid_quantity(invalid_quantity):
    warehouse = Warehouse("W-001", "Main Warehouse", {"P-001": 100})

    with pytest.raises(ValueError):
        warehouse.receive("P-001", invalid_quantity)


@pytest.mark.parametrize(
    "invalid_quantity",
    [
        0,
        -5,
        1.5,
        True,
        "10",
        None,
    ],
)
def test_ship_rejects_invalid_quantity(invalid_quantity):
    warehouse = Warehouse("W-001", "Main Warehouse", {"P-001": 100})

    with pytest.raises(ValueError):
        warehouse.ship("P-001", invalid_quantity)


def test_warehouse_needs_reorder():
    warehouse = Warehouse("W-001", "Main Warehouse", {"P-001": 20})

    assert warehouse.needs_reorder("P-001", 25, 0) is True
    assert warehouse.needs_reorder("P-001", 25, 10) is False


# ============================================================
# B-06: Economic Order Quantity (EOQ)
# Test Cases: TC-INV-07 to TC-INV-10
# ============================================================

SAMPLE_CONFIG = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "sample_config.json"
)


def sample_product(product_id):
    cfg = json.loads(SAMPLE_CONFIG.read_text(encoding="utf-8"))
    return next(
        product
        for product in cfg["products"]
        if product["product_id"] == product_id
    )


def test_eoq_known_value():
    """TC-INV-07: Validate EOQ calculation and integer rounding."""

    assert economic_order_quantity(1000, 50, 2) == 224
    assert isinstance(economic_order_quantity(1000, 50, 2), int)
    assert economic_order_quantity(1000.0, 50.0, 2.0) == 224
    assert economic_order_quantity(100, 2, 4) == 10

    # P-001: forecast of 20 units per day, annualized.
    p001 = sample_product("P-001")

    assert economic_order_quantity(
        20 * 365,
        p001["order_cost"],
        p001["holding_cost_per_day"] * 365,
    ) == 200

    assert economic_order_quantity(0.5, 1, 1000) == 1
    assert economic_order_quantity(1000, 0, 2) == 0


def test_eoq_zero_demand():
    """TC-INV-08: Zero demand gives zero EOQ."""

    assert economic_order_quantity(0, 50, 2) == 0
    assert economic_order_quantity(0.0, 50, 2) == 0
    assert economic_order_quantity(0, 0, 2) == 0


@pytest.mark.parametrize(
    "bad_value",
    [
        0,
        0.0,
        -2,
        True,
        "2",
        None,
        float("nan"),
        float("inf"),
    ],
)
def test_eoq_invalid_holding_cost(bad_value):
    """TC-INV-09: Invalid holding costs must raise ValueError."""

    with pytest.raises(
        ValueError,
        match="annual_holding_cost_per_unit",
    ):
        economic_order_quantity(1000, 50, bad_value)


@pytest.mark.parametrize(
    "field,args",
    [
        ("annual_demand", (-5, 50, 2)),
        ("annual_demand", (-0.1, 50, 2)),
        ("annual_demand", (True, 50, 2)),
        ("annual_demand", ("1000", 50, 2)),
        ("annual_demand", (float("nan"), 50, 2)),
        ("annual_demand", (float("inf"), 50, 2)),
        ("order_cost", (1000, -1, 2)),
        ("order_cost", (1000, False, 2)),
        ("order_cost", (1000, None, 2)),
        ("order_cost", (1000, float("-inf"), 2)),
    ],
)
def test_eoq_invalid_demand_or_order_cost(field, args):
    """TC-INV-10: Invalid demand or order cost must raise ValueError."""

    with pytest.raises(ValueError, match=field):
        economic_order_quantity(*args)


# ============================================================
# B-16: Safety Stock and Reorder Point
# Test Cases: TC-INV-11 to TC-INV-15
# ============================================================

def test_safety_stock_calculation():
    assert safety_stock(1.65, 10, 4) == 33


def test_safety_stock_zero_variability():
    assert safety_stock(1.65, 0, 4) == 0


def test_reorder_point_calculation():
    assert reorder_point(20, 5, 30) == 130


def test_reorder_point_rounds_up():
    assert reorder_point(10.5, 3, 5) == 37


def test_warehouse_reorder_decision():
    warehouse = Warehouse("W-001", "Main Warehouse", {"P-001": 50})

    assert warehouse.needs_reorder("P-001", 60, 0) is True
    assert warehouse.needs_reorder("P-001", 60, 20) is False


@pytest.mark.parametrize(
    "function,args",
    [
        (safety_stock, (-1, 10, 4)),
        (safety_stock, (1.65, -10, 4)),
        (safety_stock, (1.65, 10, -4)),
        (safety_stock, (True, 10, 4)),
        (safety_stock, (1.65, float("inf"), 4)),
        (reorder_point, (-10, 5, 30)),
        (reorder_point, (20, -5, 30)),
        (reorder_point, (20, 5, -30)),
        (reorder_point, (True, 5, 30)),
        (reorder_point, (20, float("nan"), 30)),
    ],
)
def test_invalid_safety_stock_and_reorder_inputs(function, args):
    with pytest.raises(ValueError):
        function(*args)
