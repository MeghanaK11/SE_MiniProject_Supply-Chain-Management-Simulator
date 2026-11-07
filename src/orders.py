"""Customer orders for the supply chain simulator (SCM-F-021).

The order book and FIFO allocation (SCM-F-022, SCM-F-023) are added to this
module in later backlog items.
"""
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
