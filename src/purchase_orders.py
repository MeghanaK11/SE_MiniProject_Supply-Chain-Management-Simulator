"""Purchase orders for the supply chain simulator (SCM-F-013).
 
The PO lifecycle and purchase order book (SCM-F-014) and random supplier
delays (SCM-F-015) are added to this module in later backlog items.
"""
from dataclasses import dataclass
 
from src.suppliers import Supplier
 
PLACED = "PLACED"
 
 
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
 
    @property
    def total_cost(self) -> float:
        """Quantity times unit price, in rupees."""
        return self.quantity * self.unit_price
 
 
def create_purchase_order(po_id: str, supplier: Supplier, product_id: str,
                          quantity: int, order_day: int) -> PurchaseOrder:
    """Create a PLACED purchase order priced and timed from the supplier.
 
    Raises ValueError for a blank po_id, a quantity outside 1 to
    supplier.max_order_qty, or a product the supplier does not sell.
    """
    if not isinstance(po_id, str) or not po_id.strip():
        raise ValueError("po_id must be a non-empty string")
    if not _is_int(quantity) or not 1 <= quantity <= supplier.max_order_qty:
        raise ValueError(
            f"quantity must be a whole number from 1 to {supplier.max_order_qty} "
            f"for supplier {supplier.supplier_id}, got {quantity!r}"
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
 