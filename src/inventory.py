
"""Inventory rules for the supply chain simulator.

Includes:
- B-06: Economic Order Quantity (EOQ)
- B-07: Warehouse stock management
- B-16: Safety stock and reorder point
"""

import math


def _check_number(name: str, value) -> None:
    """Reject bool, text, NaN and infinity; only finite ints and floats pass."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError(f"{name} must be a finite number, got {value!r}")


def economic_order_quantity(
    annual_demand: float,
    order_cost: float,
    annual_holding_cost_per_unit: float,
) -> int:
    """Calculate EOQ using ceil(sqrt(2 * D * S / H))."""
    _check_number("annual_demand", annual_demand)
    _check_number("order_cost", order_cost)
    _check_number(
        "annual_holding_cost_per_unit",
        annual_holding_cost_per_unit,
    )

    if annual_holding_cost_per_unit <= 0:
        raise ValueError(
            "annual_holding_cost_per_unit must be greater than 0, "
            f"got {annual_holding_cost_per_unit!r}"
        )

    if annual_demand < 0:
        raise ValueError(
            f"annual_demand must be 0 or more, got {annual_demand!r}"
        )

    if order_cost < 0:
        raise ValueError(
            f"order_cost must be 0 or more, got {order_cost!r}"
        )

    if annual_demand == 0:
        return 0

    root = math.sqrt(
        2 * annual_demand * order_cost
        / annual_holding_cost_per_unit
    )

    # Preserve B-06 rounding behaviour.
    return math.ceil(round(root, 9))


class Warehouse:
    """Track inventory for multiple products in a warehouse."""

    def __init__(self, warehouse_id, name, initial_stock=None):
        if not isinstance(warehouse_id, str) or not warehouse_id.strip():
            raise ValueError("Warehouse ID must be a non-empty string")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Warehouse name must be a non-empty string")

        if initial_stock is None:
            initial_stock = {}

        if not isinstance(initial_stock, dict):
            raise ValueError("Initial stock must be a dictionary")

        self.warehouse_id = warehouse_id
        self.name = name
        self._stock = {}

        for product_id, quantity in initial_stock.items():
            self._validate_product_id(product_id)

            if type(quantity) is not int or quantity < 0:
                raise ValueError(
                    "Initial stock must be a non-negative integer"
                )

            self._stock[product_id] = quantity

    @staticmethod
    def _validate_product_id(product_id):
        if not isinstance(product_id, str) or not product_id.strip():
            raise ValueError("Product ID must be a non-empty string")

    def receive(self, product_id, qty):
        """Increase stock when new inventory arrives."""
        self._validate_product_id(product_id)

        if type(qty) is not int or qty <= 0:
            raise ValueError("Quantity must be a positive integer")

        self._stock[product_id] = self._stock.get(product_id, 0) + qty

    def ship(self, product_id, qty):
        """Ship available stock without allowing inventory to become negative."""
        self._validate_product_id(product_id)

        if type(qty) is not int or qty <= 0:
            raise ValueError("Quantity must be a positive integer")

        available = self._stock.get(product_id, 0)
        shipped = min(qty, available)
        self._stock[product_id] = available - shipped

        return shipped

    def stock_level(self, product_id):
        """Return current stock for a product."""
        self._validate_product_id(product_id)
        return self._stock.get(product_id, 0)

    def snapshot(self):
        """Return a copy of the current inventory."""
        return self._stock.copy()

    def needs_reorder(self, product_id, reorder_point, on_order=0):
        """Check whether stock plus outstanding orders is at or below ROP."""
        self._validate_product_id(product_id)

        if type(reorder_point) is not int or reorder_point < 0:
            raise ValueError(
                "Reorder point must be a non-negative integer"
            )

        if type(on_order) is not int or on_order < 0:
            raise ValueError(
                "On-order quantity must be a non-negative integer"
            )

        return self.stock_level(product_id) + on_order <= reorder_point


def safety_stock(z, demand_std_per_day, lead_time_days):
    """Calculate safety stock and round up to the next whole unit."""
    values = (z, demand_std_per_day, lead_time_days)

    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
        for value in values
    ):
        raise ValueError("Inputs must be finite non-negative numbers")

    result = z * demand_std_per_day * math.sqrt(lead_time_days)
    return math.ceil(round(result, 6))


def reorder_point(avg_daily_demand, lead_time_days, safety_stock_units):
    """Calculate reorder point and round up to the next whole unit."""
    values = (
        avg_daily_demand,
        lead_time_days,
        safety_stock_units,
    )

    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
        for value in values
    ):
        raise ValueError("Inputs must be finite non-negative numbers")

    result = (
        avg_daily_demand * lead_time_days + safety_stock_units
    )
    return math.ceil(round(result, 6))
