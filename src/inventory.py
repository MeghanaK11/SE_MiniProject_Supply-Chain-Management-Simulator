"""Warehouse inventory management."""

from typing import Optional


class Warehouse:
    """Tracks stock quantities for products in a warehouse."""

    def __init__(
        self,
        warehouse_id: str,
        name: str,
        initial_stock: Optional[dict[str, int]] = None,
    ) -> None:
        """Create a warehouse with optional initial product stock."""
        if not isinstance(warehouse_id, str) or not warehouse_id.strip():
            raise ValueError("warehouse_id must be a non-empty string")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        if initial_stock is None:
            initial_stock = {}

        if not isinstance(initial_stock, dict):
            raise ValueError("initial_stock must be a dictionary")

        for product_id, quantity in initial_stock.items():
            if not isinstance(product_id, str) or not product_id.strip():
                raise ValueError("product IDs must be non-empty strings")

            if type(quantity) is not int or quantity < 0:
                raise ValueError(
                    "initial stock quantities must be non-negative integers"
                )

        self.warehouse_id = warehouse_id
        self.name = name
        self._stock = initial_stock.copy()

    @staticmethod
    def _validate_quantity(qty: int) -> None:
        """Ensure a stock movement quantity is a positive integer."""
        if type(qty) is not int or qty <= 0:
            raise ValueError("quantity must be a positive integer")

    def receive(self, product_id: str, qty: int) -> int:
        """Add received units and return the updated stock level."""
        self._validate_quantity(qty)

        if not isinstance(product_id, str) or not product_id.strip():
            raise ValueError("product_id must be a non-empty string")

        self._stock[product_id] = self._stock.get(product_id, 0) + qty
        return self._stock[product_id]

    def ship(self, product_id: str, qty: int) -> int:
        """Ship available units and return the quantity actually shipped."""
        self._validate_quantity(qty)

        if not isinstance(product_id, str) or not product_id.strip():
            raise ValueError("product_id must be a non-empty string")

        available = self._stock.get(product_id, 0)
        shipped = min(available, qty)

        self._stock[product_id] = available - shipped
        return shipped

    def stock_level(self, product_id: str) -> int:
        """Return the current stock for a product, or zero if unknown."""
        if not isinstance(product_id, str) or not product_id.strip():
            raise ValueError("product_id must be a non-empty string")

        return self._stock.get(product_id, 0)

    def snapshot(self) -> dict[str, int]:
        """Return a copy of the current stock levels."""
        return self._stock.copy()