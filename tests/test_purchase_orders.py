import pytest
from types import SimpleNamespace

from src.purchase_orders import PurchaseOrder, PurchaseOrderBook


@pytest.fixture
def supplier():
    return SimpleNamespace(
        supplier_id="S1",
        lead_time_days=3,
        max_order_qty=100,
        products=["P1", "P2"],
    )


def test_purchase_order_initial_status(supplier):
    order = PurchaseOrder("PO-0001", supplier, "P1", 10, 1, 4)
    assert order.status == "PLACED"


def test_purchase_order_valid_transitions(supplier):
    order = PurchaseOrder("PO-0001", supplier, "P1", 10, 1, 4)

    order.advance("IN_TRANSIT")
    assert order.status == "IN_TRANSIT"

    order.advance("DELIVERED")
    assert order.status == "DELIVERED"


def test_purchase_order_invalid_transition(supplier):
    order = PurchaseOrder("PO-0001", supplier, "P1", 10, 1, 4)

    with pytest.raises(ValueError):
        order.advance("DELIVERED")


def test_purchase_order_book_place(supplier):
    book = PurchaseOrderBook()

    first = book.place(supplier, "P1", 20, 2)
    second = book.place(supplier, "P2", 15, 3)

    assert first.po_id == "PO-0001"
    assert second.po_id == "PO-0002"
    assert first.status == "IN_TRANSIT"
    assert first.expected_delivery_day == 5


def test_purchase_order_book_due_on(supplier):
    """TC-PO-10: Due orders are returned on or after their delivery day."""
    book = PurchaseOrderBook()

    first = book.place(supplier, "P1", 20, 1)
    second = book.place(supplier, "P1", 10, 5)

    assert book.due_on(3) == []
    assert book.due_on(4) == [first]

    first.advance("DELIVERED")

    assert book.due_on(7) == []
    assert book.due_on(8) == [second]


def test_purchase_order_book_on_order_quantity(supplier):
    book = PurchaseOrderBook()

    first = book.place(supplier, "P1", 20, 1)
    book.place(supplier, "P1", 10, 2)

    assert book.on_order_qty("P1") == 30

    first.advance("DELIVERED")

    assert book.on_order_qty("P1") == 10


def test_invalid_purchase_order_quantity(supplier):
    book = PurchaseOrderBook()

    with pytest.raises(ValueError):
        book.place(supplier, "P1", 0, 1)

    with pytest.raises(ValueError):
        book.place(supplier, "P1", 101, 1)


def test_supplier_product_validation(supplier):
    book = PurchaseOrderBook()

    with pytest.raises(ValueError):
        book.place(supplier, "UNKNOWN", 10, 1)