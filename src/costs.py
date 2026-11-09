
"""Cost tracking for the supply chain simulator (SCM-F-006)."""

import math


class CostTracker:
    """Accumulate holding, stockout, ordering, purchase and transport costs."""

    def __init__(self):
        """Initialize all cost categories to zero."""
        self.holding_cost = 0.0
        self.stockout_cost = 0.0
        self.ordering_cost = 0.0
        self.purchase_cost = 0.0
        self.transport_cost = 0.0

    def add_holding_cost(self, stock_end, product):
        """Add daily holding cost based on ending inventory."""
        self._validate_quantity(stock_end, "stock_end")
        self.holding_cost += stock_end * product.holding_cost_per_day

    def add_stockout_cost(self, backorder_qty, product):
        """Add stockout cost based on outstanding backorder quantity."""
        self._validate_quantity(backorder_qty, "backorder_qty")
        self.stockout_cost += backorder_qty * product.stockout_penalty

    def add_ordering_cost(self, product, order_count=1):
        """Add ordering cost for the specified number of orders."""
        self._validate_quantity(order_count, "order_count")
        self.ordering_cost += order_count * product.order_cost

    def add_purchase_cost(self, quantity, unit_price):
        """Add purchase cost of the specified quantity."""
        self._validate_quantity(quantity, "quantity")
        self._validate_money(unit_price, "unit_price")
        self.purchase_cost += quantity * unit_price

    def add_transport_cost(self, cost):
        """Add an already calculated transport cost."""
        self._validate_money(cost, "cost")
        self.transport_cost += cost

    @property
    def total_cost(self):
        """Return the sum of all five cost categories."""
        return (
            self.holding_cost
            + self.stockout_cost
            + self.ordering_cost
            + self.purchase_cost
            + self.transport_cost
        )

    def breakdown(self):
        """Return each cost category and the total."""
        return {
            "holding": self.holding_cost,
            "stockout": self.stockout_cost,
            "ordering": self.ordering_cost,
            "purchase": self.purchase_cost,
            "transport": self.transport_cost,
            "total": self.total_cost,
        }

    @staticmethod
    def _validate_quantity(value, name):
        """Validate a non-negative whole-number quantity."""
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
        ):
            raise ValueError(f"{name} must be a non-negative integer")

    @staticmethod
    def _validate_money(value, name):
        """Validate a finite, non-negative monetary amount."""
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(
                f"{name} must be a finite non-negative number"
            )
