import json
import random
from pathlib import Path
 
import pytest
 
from src.purchase_orders import (
    PLACED,
    IN_TRANSIT,
    DELIVERED,
    CANCELLED,
    PurchaseOrder,
    PurchaseOrderBook,
    apply_random_delay,
    create_purchase_order,
)
from src.suppliers import Supplier
 
 
SAMPLE_CONFIG = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "sample_config.json"
)
 
 
def sample_supplier(supplier_id):
    """Build a real Supplier from the sample configuration."""
    with open(SAMPLE_CONFIG, encoding="utf-8") as file:
        entries = json.load(file)["suppliers"]
 
    entry = next(
        entry for entry in entries
        if entry["supplier_id"] == supplier_id
    )
 
    return Supplier.from_dict(entry)
 
 
# --------------------------------------------------
# B-14: Purchase Order Creation
# --------------------------------------------------
 
def test_po_delivery_day():
    """TC-PO-01: Three-day lead time gives delivery day 8."""
    po = create_purchase_order(
        "PO-0001", sample_supplier("S-001"), "P-001", 100, 5
    )
 
    assert po.expected_delivery_day == 8
    assert po.order_day == 5
    assert po.status == PLACED
    assert (
        po.po_id,
        po.supplier_id,
        po.product_id,
        po.quantity,
    ) == ("PO-0001", "S-001", "P-001", 100)
 
 
def test_po_total_cost():
    """TC-PO-02: Verify total purchase order cost."""
    po = create_purchase_order(
        "PO-0001", sample_supplier("S-001"), "P-001", 100, 5
    )
 
    assert po.unit_price == 110.0
    assert po.total_cost == 11000.0
 
 
def test_po_over_capacity_rejected():
    """TC-PO-03: Reject quantities above supplier capacity."""
    supplier = sample_supplier("S-002")
 
    with pytest.raises(ValueError, match="quantity"):
        create_purchase_order(
            "PO-0001", supplier, "P-001", 201, 1
        )
 
    assert create_purchase_order(
        "PO-0002", supplier, "P-001", 200, 1
    ).quantity == 200
 
 
def test_po_product_not_supplied():
    """TC-PO-04: Reject products not sold by the supplier."""
    with pytest.raises(ValueError, match="P-003"):
        create_purchase_order(
            "PO-0001", sample_supplier("S-001"), "P-003", 10, 1
        )
 
 
@pytest.mark.parametrize("bad_qty", [0, -5, 2.5, True])
def test_po_zero_quantity(bad_qty):
    """TC-PO-05: Reject invalid quantities and blank PO IDs."""
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
    """TC-PO-06: Allow valid purchase order status transitions."""
    po = create_purchase_order(
        "PO-0001", sample_supplier("S-001"), "P-001", 10, 5
    )
 
    assert po.status == PLACED
 
    po.advance(IN_TRANSIT)
    assert po.status == IN_TRANSIT
 
    po.advance(DELIVERED)
    assert po.status == DELIVERED
 
 
def test_po_invalid_lifecycle_transitions():
    """TC-PO-07: Reject invalid and terminal-state transitions."""
    po = create_purchase_order(
        "PO-0001", sample_supplier("S-001"), "P-001", 10, 5
    )
 
    with pytest.raises(ValueError):
        po.advance(DELIVERED)
 
    assert po.status == PLACED
 
    with pytest.raises(ValueError, match="Unknown purchase order status"):
        po.advance("BOGUS")
 
    with pytest.raises(ValueError):
        po.advance(PLACED)
 
    po.advance(IN_TRANSIT)
    po.advance(DELIVERED)
 
    with pytest.raises(ValueError):
        po.advance(PLACED)
 
    assert po.status == DELIVERED
 
    cancelled = create_purchase_order(
        "PO-0002", sample_supplier("S-001"), "P-001", 10, 5
    )
    cancelled.advance(CANCELLED)
 
    with pytest.raises(ValueError):
        cancelled.advance(IN_TRANSIT)
 
    assert cancelled.status == CANCELLED
 
 
def test_po_invalid_initial_status():
    """Reject an unknown status when creating a PurchaseOrder."""
    with pytest.raises(ValueError, match="Unknown purchase order status"):
        PurchaseOrder(
            po_id="PO-0001",
            supplier_id="S-001",
            product_id="P-001",
            quantity=10,
            unit_price=110.0,
            order_day=1,
            expected_delivery_day=4,
            status="BOGUS",
        )
 
 
def test_po_book_generates_sequential_ids():
    """TC-PO-08: Generate sequential IDs and retain orders."""
    book = PurchaseOrderBook()
    supplier = sample_supplier("S-001")
 
    first = book.place(supplier, "P-001", 10, 1)
    second = book.place(supplier, "P-001", 20, 2)
 
    assert first.po_id == "PO-0001"
    assert second.po_id == "PO-0002"
 
    assert first.status == IN_TRANSIT
    assert second.status == IN_TRANSIT
 
    assert book.get("PO-0001") is first
    assert book.get("PO-0002") is second
 
    assert book.all_orders() == [first, second]
 
    with pytest.raises(KeyError):
        book.get("PO-9999")
 
    # all_orders() must return a copy, not the internal list.
    returned_orders = book.all_orders()
    returned_orders.clear()
 
    assert len(book.all_orders()) == 2
 
 
def test_po_due_on():
    """TC-PO-09: Return outstanding orders due by the specified day."""
    book = PurchaseOrderBook()
    supplier = sample_supplier("S-001")
 
    po = book.place(supplier, "P-001", 10, 5)
 
    assert po.expected_delivery_day == 8
    assert po not in book.due_on(7)
    assert po in book.due_on(8)
 
    po.advance(DELIVERED)
 
    assert po not in book.due_on(8)
 
 
@pytest.mark.parametrize("bad_day", [-1, 1.5, True, "5", None])
def test_po_due_on_rejects_invalid_day(bad_day):
    """TC-PO-09: Reject invalid day values."""
    book = PurchaseOrderBook()
 
    with pytest.raises(ValueError, match="day"):
        book.due_on(bad_day)
 
 
def test_po_on_order_quantity_excludes_closed_orders():
    """TC-PO-10: Exclude delivered and cancelled orders."""
    book = PurchaseOrderBook()
    supplier = sample_supplier("S-001")
 
    delivered = book.place(supplier, "P-001", 20, 1)
    cancelled = book.place(supplier, "P-001", 10, 2)
    outstanding = book.place(supplier, "P-001", 15, 3)
 
    delivered.advance(DELIVERED)
    cancelled.advance(CANCELLED)
 
    assert book.on_order_qty("P-001") == 15
 
    outstanding.advance(DELIVERED)
 
    assert book.on_order_qty("P-001") == 0
 
 
# --------------------------------------------------
# B-24: Random Supplier Delays
# --------------------------------------------------
 
def make_open_order(po_id="PO-0001"):
    """A PLACED order for 10 units of P-001 from S-001 on day 5, due day 8."""
    return create_purchase_order(
        po_id, sample_supplier("S-001"), "P-001", 10, 5
    )
 
 
def test_fully_reliable_never_delayed():
    """TC-PO-11: Reliability 1.0 on 100 orders gives no delays."""
    rng = random.Random(42)
    orders = [make_open_order(f"PO-{i:04d}") for i in range(1, 101)]
 
    delays = [apply_random_delay(po, 1.0, rng, 3) for po in orders]
 
    assert delays == [0] * 100
    assert all(po.expected_delivery_day == 8 for po in orders)
 
 
def test_unreliable_always_delayed():
    """TC-PO-12: Reliability 0.0 gives a delay of 1 to 3 days every time."""
    rng = random.Random(42)
 
    for i in range(1, 101):
        po = make_open_order(f"PO-{i:04d}")
        if i % 2 == 0:
            po.advance(IN_TRANSIT)
 
        delay = apply_random_delay(po, 0.0, rng, 3)
 
        assert 1 <= delay <= 3
        assert po.expected_delivery_day == 8 + delay
 
 
def test_same_seed_same_delays():
    """TC-PO-13: Two random.Random(42) give identical delay lists."""
    def run():
        rng = random.Random(42)
        return [
            apply_random_delay(make_open_order(f"PO-{i:04d}"), 0.5, rng, 3)
            for i in range(1, 51)
        ]
 
    first = run()
    second = run()
 
    assert first == second
    assert any(d == 0 for d in first)
    assert any(d > 0 for d in first)
 
 
@pytest.mark.parametrize(
    "bad_args", [(1.5, 3), (-0.1, 3), (True, 3), (0.9, 0), (0.9, 2.5)]
)
def test_delivered_order_rejected(bad_args):
    """TC-PO-14: Reject closed orders and invalid delay settings."""
    rng = random.Random(42)
 
    delivered = make_open_order()
    delivered.advance(IN_TRANSIT)
    delivered.advance(DELIVERED)
 
    cancelled = make_open_order("PO-0002")
    cancelled.advance(CANCELLED)
 
    for closed in (delivered, cancelled):
        with pytest.raises(ValueError, match=closed.status):
            apply_random_delay(closed, 0.5, rng, 3)
        assert closed.expected_delivery_day == 8
 
    reliability, max_delay = bad_args
    with pytest.raises(ValueError):
        apply_random_delay(
            make_open_order("PO-0003"), reliability, rng, max_delay
        )
 