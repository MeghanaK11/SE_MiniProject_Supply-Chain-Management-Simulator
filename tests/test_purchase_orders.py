
import json
from pathlib import Path

import pytest

from src.purchase_orders import (
    PLACED,
    IN_TRANSIT,
    DELIVERED,
    CANCELLED,
    PurchaseOrderBook,
    create_purchase_order,
)
from src.suppliers import Supplier


SAMPLE_CONFIG = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "sample_config.json"
)


def sample_supplier(supplier_id):
    """Build the real Supplier from the sample configuration."""
    with open(SAMPLE_CONFIG, encoding="utf-8") as file:
        entries = json.load(file)["suppliers"]

    return Supplier.from_dict(
        next(
            entry for entry in entries
            if entry["supplier_id"] == supplier_id
        )
    )


# --------------------------------------------------
# B-14: Purchase Order Creation (Rushmitha's tests)
# --------------------------------------------------

def test_po_delivery_day():
    """TC-PO-01: Three-day lead time, order day 5 gives delivery day 8."""
    po = create_purchase_order(
        "PO-0001", sample_supplier("S-001"), "P-001", 100, 5
    )

    assert po.expected_delivery_day == 8
    assert po.order_day == 5
    assert po.status == PLACED
    assert (
        po.po_id, po.supplier_id, po.product_id, po.quantity
    ) == ("PO-0001", "S-001", "P-001", 100)


def test_po_total_cost():
    """TC-PO-02: 100 units of P-001 from S-001 cost Rs 11,000."""
    po = create_purchase_order(
        "PO-0001", sample_supplier("S-001"), "P-001", 100, 5
    )

    assert po.unit_price == 110.0
    assert po.total_cost == 11000.0


def test_po_over_capacity_rejected():
    """TC-PO-03: Reject quantity above supplier maximum."""
    supplier = sample_supplier("S-002")

    with pytest.raises(ValueError, match="quantity"):
        create_purchase_order("PO-0001", supplier, "P-001", 201, 1)

    assert create_purchase_order(
        "PO-0002", supplier, "P-001", 200, 1
    ).quantity == 200


def test_po_product_not_supplied():
    """TC-PO-04: Reject a product not supplied by the selected supplier."""
    with pytest.raises(ValueError, match="P-003"):
        create_purchase_order(
            "PO-0001", sample_supplier("S-001"), "P-003", 10, 1
        )


@pytest.mark.parametrize("bad_qty", [0, -5, 2.5, True])
def test_po_zero_quantity(bad_qty):
    """TC-PO-05: Reject invalid quantities and blank purchase order IDs."""
    supplier = sample_supplier("S-001")

    with pytest.raises(ValueError, match="quantity"):
        create_purchase_order(
            "PO-0001", supplier, "P-001", bad_qty, 1
        )

    with pytest.raises(ValueError, match="po_id"):
        create_purchase_order(
            "  ", supplier, "P-001", 10, 1
        )


# --------------------------------------------------
# B-17: Purchase Order Lifecycle and Book
# --------------------------------------------------

def test_po_valid_lifecycle_transitions():
    """TC-PO-06: Allow PLACED -> IN_TRANSIT -> DELIVERED."""
    po = create_purchase_order(
        "PO-0001", sample_supplier("S-001"), "P-001", 10, 5
    )

    assert po.status == PLACED

    po.advance(IN_TRANSIT)
    assert po.status == IN_TRANSIT

    po.advance(DELIVERED)
    assert po.status == DELIVERED


def test_po_invalid_lifecycle_transitions():
    """TC-PO-07: Reject invalid transitions and terminal-state changes."""
    po = create_purchase_order(
        "PO-0001", sample_supplier("S-001"), "P-001", 10, 5
    )

    with pytest.raises(ValueError):
        po.advance(DELIVERED)

    assert po.status == PLACED

    po.advance(CANCELLED)

    with pytest.raises(ValueError):
        po.advance(IN_TRANSIT)

    assert po.status == CANCELLED


def test_po_on_order_quantity_excludes_closed_orders():
    """TC-PO-08: Exclude delivered and cancelled orders from on-order quantity."""
    book = PurchaseOrderBook()
    supplier = sample_supplier("S-001")

    delivered = book.place(supplier, "P-001", 20, 1)
    cancelled = book.place(supplier, "P-001", 10, 2)
    outstanding = book.place(supplier, "P-001", 15, 3)

    delivered.advance(IN_TRANSIT)
    delivered.advance(DELIVERED)

    cancelled.advance(CANCELLED)

    assert book.on_order_qty("P-001") == 15

    outstanding.advance(IN_TRANSIT)
    assert book.on_order_qty("P-001") == 15


def test_po_released_only_on_expected_delivery_day():
    """TC-PO-09: An order due on day 8 is absent on day 7 and present on day 8."""
    book = PurchaseOrderBook()
    supplier = sample_supplier("S-001")

    # S-001 has a three-day lead time.
    po = book.place(supplier, "P-001", 10, 5)

    assert po.expected_delivery_day == 8
    assert po not in book.due_on(7)
    assert po in book.due_on(8)


def test_po_book_generates_sequential_ids():
    """TC-PO-10: Generate sequential IDs and retain orders in the book."""
    book = PurchaseOrderBook()
    supplier = sample_supplier("S-001")

    first = book.place(supplier, "P-001", 10, 1)
    second = book.place(supplier, "P-001", 20, 2)

    assert first.po_id == "PO-0001"
    assert second.po_id == "PO-0002"

    assert book.orders == [first, second]
    assert first.status == PLACED
    assert second.status == PLACED
