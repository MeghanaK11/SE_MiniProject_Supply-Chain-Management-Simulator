
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

def test_receive_10_into_empty_stock():
    """TC-INV-01: Receive 10 units into empty stock."""
    warehouse = Warehouse("W-001", "Main Warehouse")

    warehouse.receive("P-001", 10)

    assert warehouse.stock_level("P-001") == 10


def test_ship_4_from_stock_of_10():
    """TC-INV-02: Ship 4 units from stock of 10."""
    warehouse = Warehouse(
        "W-001", "Main Warehouse", {"P-001": 10}
    )

    shipped = warehouse.ship("P-001", 4)

    assert shipped == 4
    assert warehouse.stock_level("P-001") == 6


def test_ship_8_from_stock_of_5():
    """TC-INV-03: Ship only available stock."""
    warehouse = Warehouse(
        "W-001", "Main Warehouse", {"P-001": 5}
    )

    shipped = warehouse.ship("P-001", 8)

    assert shipped == 5
    assert warehouse.stock_level("P-001") == 0


@pytest.mark.parametrize(
    "operation, product_id, quantity",
    [
        ("receive", "P-001", 0),
        ("ship", "P-001", -2),
    ],
)
def test_invalid_receive_or_ship_quantity(
    operation, product_id, quantity
):
    """TC-INV-04: Invalid receive and ship quantities raise ValueError."""
    warehouse = Warehouse("W-001", "Main Warehouse")

    with pytest.raises(ValueError):
        getattr(warehouse, operation)(product_id, quantity)


def test_unknown_product_stock_level_is_zero():
    """TC-INV-05: Unknown product has stock level zero."""
    warehouse = Warehouse("W-001", "Main Warehouse")

    assert warehouse.stock_level("P-999") == 0


def test_snapshot_returns_independent_copy():
    """TC-INV-06: Snapshot is a copy of warehouse stock."""
    warehouse = Warehouse(
        "W-001", "Main Warehouse", {"P-001": 10}
    )

    snapshot = warehouse.snapshot()
    snapshot["P-001"] = 500
    snapshot["P-002"] = 20

    assert warehouse.stock_level("P-001") == 10
    assert warehouse.stock_level("P-002") == 0


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
    """TC-INV-09: Invalid holding costs raise ValueError."""
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
    """TC-INV-10: Invalid demand or order cost raises ValueError."""
    with pytest.raises(ValueError, match=field):
        economic_order_quantity(*args)


# ============================================================
# B-16: Safety Stock and Reorder Point
# Test Cases: TC-INV-11 to TC-INV-15
# ============================================================

def test_safety_stock_calculation():
    """TC-INV-11: Calculate safety stock."""
    assert safety_stock(1.65, 4, 4) == 14


def test_reorder_point_calculation():
    """TC-INV-12: Calculate reorder point."""
    assert reorder_point(10, 4, 14) == 54


def test_needs_reorder_without_outstanding_order():
    """TC-INV-13: Reorder when stock is below ROP."""
    warehouse = Warehouse(
        "W-001", "Main Warehouse", {"P-001": 50}
    )

    assert warehouse.needs_reorder("P-001", 54, 0) is True


def test_no_reorder_when_outstanding_order_covers_gap():
    """TC-INV-14: Do not reorder when on-order stock covers the gap."""
    warehouse = Warehouse(
        "W-001", "Main Warehouse", {"P-001": 50}
    )

    assert warehouse.needs_reorder("P-001", 54, 10) is False


@pytest.mark.parametrize(
    "function,args",
    [
        (safety_stock, (1.65, -4, 4)),
        (safety_stock, (1.65, 4, -4)),
        (reorder_point, (10, -4, 14)),
    ],
)
def test_negative_std_or_lead_time_raises_value_error(
    function, args
):
    """TC-INV-15: Negative standard deviation or lead time is invalid."""
    with pytest.raises(ValueError):
        function(*args)


# ============================================================
# Additional input validation tests
# ============================================================

@pytest.mark.parametrize(
    "invalid_product_id",
    [None, "", "   ", 123, True],
)
def test_receive_rejects_invalid_product_id(invalid_product_id):
    warehouse = Warehouse("W-001", "Main Warehouse")

    with pytest.raises(ValueError):
        warehouse.receive(invalid_product_id, 5)


@pytest.mark.parametrize(
    "invalid_product_id",
    [None, "", "   ", 123, True],
)
def test_ship_rejects_invalid_product_id(invalid_product_id):
    warehouse = Warehouse("W-001", "Main Warehouse")

    with pytest.raises(ValueError):
        warehouse.ship(invalid_product_id, 5)


@pytest.mark.parametrize(
    "invalid_product_id",
    [None, "", "   ", 123, True],
)
def test_stock_level_rejects_invalid_product_id(invalid_product_id):
    warehouse = Warehouse("W-001", "Main Warehouse")

    with pytest.raises(ValueError):
        warehouse.stock_level(invalid_product_id)


@pytest.mark.parametrize(
    "invalid_product_id",
    [None, "", "   ", 123, True],
)
def test_needs_reorder_rejects_invalid_product_id(
    invalid_product_id
):
    warehouse = Warehouse("W-001", "Main Warehouse")

    with pytest.raises(ValueError):
        warehouse.needs_reorder(invalid_product_id, 10)


def test_initial_stock_defaults_to_empty():
    warehouse = Warehouse("W-001", "Main Warehouse")

    assert warehouse.snapshot() == {}


@pytest.mark.parametrize(
    "function,args",
    [
        (safety_stock, (1.65, float("inf"), 4)),
        (safety_stock, (1.65, float("nan"), 4)),
        (safety_stock, (1.65, 4, float("inf"))),
        (safety_stock, (1.65, 4, float("nan"))),
        (reorder_point, (float("inf"), 4, 14)),
        (reorder_point, (float("nan"), 4, 14)),
        (reorder_point, (10, float("inf"), 14)),
        (reorder_point, (10, float("nan"), 14)),
        (reorder_point, (10, 4, float("inf"))),
        (reorder_point, (10, 4, float("nan"))),
    ],
)
def test_safety_stock_and_reorder_point_reject_non_finite_values(
    function, args
):
    with pytest.raises(ValueError):
        function(*args)


def test_reorder_point_avoids_floating_point_over_rounding():
    assert reorder_point(29 / 7, 7, 0) == 29


def test_needs_reorder_defaults_on_order_to_zero():
    warehouse = Warehouse(
        "W-001", "Main Warehouse", {"P-001": 50}
    )

    assert warehouse.needs_reorder("P-001", 54) is True
