"""Customer orders, the order book and FIFO allocation (SCM-F-021, SCM-F-022, SCM-F-023)."""
from dataclasses import dataclass

PENDING = "PENDING"
PARTIAL = "PARTIAL"
FULFILLED = "FULFILLED"
STATUSES = (PENDING, PARTIAL, FULFILLED)


def _is_int(value) -> bool:
    """True for real integers; bool is excluded on purpose."""
    return isinstance(value, int) and not isinstance(value, bool)


def _status_for(fulfilled_qty: int, quantity: int) -> str:
    """The only status that is consistent with the shipped amount."""
    if fulfilled_qty == 0:
        return PENDING
    return FULFILLED if fulfilled_qty == quantity else PARTIAL


@dataclass
class CustomerOrder:
    """One customer order and how much of it has been shipped so far."""

    order_id: str
    product_id: str
    quantity: int
    day: int
    fulfilled_qty: int = 0
    status: str = PENDING

    def __post_init__(self):
        for field in ("order_id", "product_id"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty string")
        if not _is_int(self.quantity) or self.quantity < 1:
            raise ValueError(f"quantity must be an integer of at least 1, got {self.quantity!r}")
        if not _is_int(self.day) or self.day < 0:
            raise ValueError(f"day must be an integer of 0 or more, got {self.day!r}")
        if not _is_int(self.fulfilled_qty) or not 0 <= self.fulfilled_qty <= self.quantity:
            raise ValueError(
                f"fulfilled_qty must be an integer from 0 to {self.quantity}, got {self.fulfilled_qty!r}"
            )
        if self.status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}, got {self.status!r}")
        expected = _status_for(self.fulfilled_qty, self.quantity)
        if self.status != expected:
            raise ValueError(
                f"status {self.status} does not match fulfilled_qty {self.fulfilled_qty}; expected {expected}"
            )

    @property
    def remaining(self) -> int:
        """Units still owed to the customer."""
        return self.quantity - self.fulfilled_qty

    def apply_shipment(self, qty: int) -> None:
        """Record a shipment of qty units and update the status."""
        if not _is_int(qty) or qty < 1 or qty > self.remaining:
            raise ValueError(
                f"shipment must be an integer from 1 to {self.remaining}, got {qty!r}"
            )
        self.fulfilled_qty += qty
        self.status = _status_for(self.fulfilled_qty, self.quantity)


class OrderBook:
    """All customer orders, numbered CO-0001, CO-0002, ... and kept oldest first (SCM-F-022)."""

    def __init__(self):
        self._orders = {}  # dicts keep insertion order, so this is oldest first

    def create(self, product_id: str, quantity: int, day: int) -> CustomerOrder:
        """Create the next numbered order, store it and return it."""
        order = CustomerOrder(
            order_id=f"CO-{len(self._orders) + 1:04d}",
            product_id=product_id,
            quantity=quantity,
            day=day,
        )
        self._orders[order.order_id] = order
        return order

    def get(self, order_id: str) -> CustomerOrder:
        """Return the order with this ID; KeyError if it is unknown."""
        if order_id not in self._orders:
            raise KeyError(f"unknown order_id '{order_id}'")
        return self._orders[order_id]

    def open_orders(self, product_id: str = None) -> list:
        """Orders not yet fulfilled, oldest first by day then order_id; optionally one product only."""
        return sorted(
            (
                order for order in self._orders.values()
                if order.status != FULFILLED
                and (product_id is None or order.product_id == product_id)
            ),
            key=lambda o: (o.day, o.order_id),
        )

    def all_orders(self) -> list:
        """Every order, oldest first."""
        return list(self._orders.values())

    def allocate(self, product_id: str, available_qty: int) -> int:
        """Give available_qty units to this product's open orders, oldest first (FIFO).

        Each order gets as much as it still needs until the stock runs out.
        Returns the total number of units allocated.
        """
        if not _is_int(available_qty) or available_qty < 0:
            raise ValueError(
                f"available_qty must be an integer of 0 or more, got {available_qty!r}"
            )
        allocated = 0
        for order in self.open_orders(product_id):
            if available_qty == 0:
                break
            qty = min(order.remaining, available_qty)
            order.apply_shipment(qty)
            available_qty -= qty
            allocated += qty
        return allocated

    def backorder_qty(self, product_id: str) -> int:
        """Units still owed on this product's open orders."""
        return sum(order.remaining for order in self.open_orders(product_id))