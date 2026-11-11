
"""Purchase orders for the supply chain simulator (SCM-F-013/014)."""

from dataclasses import dataclass

from src.suppliers import Supplier


PLACED = "PLACED"
IN_TRANSIT = "IN_TRANSIT"
DELIVERED = "DELIVERED"
CANCELLED = "CANCELLED"


def _is_int(value) -> bool:
    """True for real integers; bool is excluded on purpose."""
    return isinstance(value, int) and not isinstance(value, bool)


@dataclass
class PurchaseOrder:
    """One order to a supplier for one product."""

    po_id: str
    supplier_id: str
    product_id: str
    quantity: int
    unit_price: float
    order_day: int
    expected_delivery_day: int
    status: str = PLACED

    VALID_STATUSES = {
        PLACED,
        IN_TRANSIT,
        DELIVERED,
        CANCELLED,
    }

    TRANSITIONS = {
        PLACED: {IN_TRANSIT, CANCELLED},
        IN_TRANSIT: {DELIVERED, CANCELLED},
        DELIVERED: set(),
        CANCELLED: set(),
    }

    @property
    def total_cost(self) -> float:
        """Quantity multiplied by unit price."""
        return self.quantity * self.unit_price

    def advance(self, new_status: str) -> None:
        """Move the purchase order to a permitted next status."""
        if (
            not isinstance(new_status, str)
            or new_status not in self.VALID_STATUSES
        ):
            raise ValueError("Unknown purchase order status")

        if new_status not in self.TRANSITIONS[self.status]:
            raise ValueError(
                f"Cannot transition from {self.status} to {new_status}"
            )

        self.status = new_status


def create_purchase_order(
    po_id: str,
    supplier: Supplier,
    product_id: str,
    quantity: int,
    order_day: int,
) -> PurchaseOrder:
    """Create a PLACED purchase order priced and timed from the supplier.

    Raises ValueError for a blank po_id, a quantity outside 1 to
    supplier.max_order_qty, or a product the supplier does not sell.
    """
    if not isinstance(po_id, str) or not po_id.strip():
        raise ValueError("po_id must be a non-empty string")

    if (
        not _is_int(quantity)
        or not 1 <= quantity <= supplier.max_order_qty
    ):
        raise ValueError(
            f"quantity must be a whole number from 1 to "
            f"{supplier.max_order_qty} for supplier "
            f"{supplier.supplier_id}, got {quantity!r}"
        )

    try:
        unit_price = supplier.price_for(product_id)
    except KeyError:
        raise ValueError(
            f"supplier {supplier.supplier_id} does not supply {product_id}"
        ) from None

    return PurchaseOrder(
        po_id=po_id,
        supplier_id=supplier.supplier_id,
        product_id=product_id,
        quantity=quantity,
        unit_price=unit_price,
        order_day=order_day,
        expected_delivery_day=order_day + supplier.lead_time_days,
    )


class PurchaseOrderBook:
    """Create and track purchase orders."""

    def __init__(self):
        self.orders = []
        self._next_id = 1

    def place(
        self,
        supplier: Supplier,
        product_id: str,
        quantity: int,
        order_day: int,
    ) -> PurchaseOrder:
        """Create, register, and dispatch a purchase order."""
        po_id = f"PO-{self._next_id:04d}"

        order = create_purchase_order(
            po_id=po_id,
            supplier=supplier,
            product_id=product_id,
            quantity=quantity,
            order_day=order_day,
        )

        order.advance(IN_TRANSIT)

        self.orders.append(order)
        self._next_id += 1

        return order

    def get(self, po_id: str) -> PurchaseOrder:
        """Retrieve an order by ID; raise KeyError if it does not exist."""
        for order in self.orders:
            if order.po_id == po_id:
                return order

        raise KeyError(f"unknown purchase order ID: {po_id}")

    def due_on(self, day: int) -> list:
        """Return outstanding orders due on or before the given day."""
        if not _is_int(day) or day < 0:
            raise ValueError("day must be a non-negative integer")

        return sorted(
            [
                order
                for order in self.orders
                if order.status in (PLACED, IN_TRANSIT)
                and order.expected_delivery_day <= day
            ],
            key=lambda order: order.po_id,
        )

    def on_order_qty(self, product_id: str) -> int:
        """Return outstanding quantity for the specified product."""
        return sum(
            order.quantity
            for order in self.orders
            if order.product_id == product_id
            and order.status in (PLACED, IN_TRANSIT)
        )

    def all_orders(self) -> list:
        """Return all purchase orders in insertion order."""
        return list(self.orders)
