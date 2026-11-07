"""Customer orders for the supply chain simulator (SCM-F-021).

The order book and FIFO allocation (SCM-F-022, SCM-F-023) are added to this
module in later backlog items.
"""
from dataclasses import dataclass

PENDING = "PENDING"
PARTIAL = "PARTIAL"
FULFILLED = "FULFILLED"


def _is_int(value) -> bool:
    """True for real integers; bool is excluded on purpose."""
    return isinstance(value, int) and not isinstance(value, bool)


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
        if not _is_int(self.quantity) or self.quantity < 1:
            raise ValueError(f"quantity must be an integer of at least 1, got {self.quantity!r}")

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
        self.status = FULFILLED if self.remaining == 0 else PARTIAL
