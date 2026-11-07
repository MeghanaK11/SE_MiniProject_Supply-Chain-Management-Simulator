import math


class Warehouse:
    """Track inventory for multiple products in a warehouse."""

    def __init__(self, warehouse_id, name, initial_stock):
        if not isinstance(warehouse_id, str) or not warehouse_id:
            raise ValueError("Warehouse ID must be a non-empty string")

        if not isinstance(name, str) or not name:
            raise ValueError("Warehouse name must be a non-empty string")

        if not isinstance(initial_stock, dict):
            raise ValueError("Initial stock must be a dictionary")

        self.warehouse_id = warehouse_id
        self.name = name
        self._stock = {}

        for product_id, quantity in initial_stock.items():
            if not isinstance(product_id, str) or not product_id:
                raise ValueError("Product ID must be a non-empty string")

            if type(quantity) is not int or quantity < 0:
                raise ValueError("Initial stock must be a non-negative integer")

            self._stock[product_id] = quantity

    def receive(self, product_id, qty):
        """Increase stock when new inventory arrives."""
        if type(qty) is not int or qty <= 0:
            raise ValueError("Quantity must be a positive integer")

        self._stock[product_id] = self._stock.get(product_id, 0) + qty

    def ship(self, product_id, qty):
        """Ship available stock without allowing inventory to become negative."""
        if type(qty) is not int or qty <= 0:
            raise ValueError("Quantity must be a positive integer")

        available = self._stock.get(product_id, 0)
        shipped = min(qty, available)

        self._stock[product_id] = available - shipped

        return shipped

    def stock_level(self, product_id):
        """Return current stock for a product."""
        return self._stock.get(product_id, 0)

    def snapshot(self):
        """Return a copy of the current inventory."""
        return self._stock.copy()

    def needs_reorder(self, product_id, reorder_point, on_order):
        """Check whether stock plus outstanding orders has reached reorder point."""
        if type(reorder_point) is not int or reorder_point < 0:
            raise ValueError("Reorder point must be a non-negative integer")

        if type(on_order) is not int or on_order < 0:
            raise ValueError("On-order quantity must be a non-negative integer")

        return self.stock_level(product_id) + on_order <= reorder_point


def safety_stock(z, demand_std_per_day, lead_time_days):
    """Calculate safety stock and round it up to the next whole unit."""
    if (
        isinstance(z, bool)
        or isinstance(demand_std_per_day, bool)
        or isinstance(lead_time_days, bool)
        or not isinstance(z, (int, float))
        or not isinstance(demand_std_per_day, (int, float))
        or not isinstance(lead_time_days, (int, float))
        or z < 0
        or demand_std_per_day < 0
        or lead_time_days < 0
    ):
        raise ValueError("Inputs must be non-negative numbers")

    return math.ceil(
        z * demand_std_per_day * math.sqrt(lead_time_days)
    )


def reorder_point(avg_daily_demand, lead_time_days, safety_stock_units):
    """Calculate reorder point and round it up to the next whole unit."""
    values = (avg_daily_demand, lead_time_days, safety_stock_units)

    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or value < 0
        for value in values
    ):
        raise ValueError("Inputs must be non-negative numbers")

    return math.ceil(
        avg_daily_demand * lead_time_days + safety_stock_units
    )