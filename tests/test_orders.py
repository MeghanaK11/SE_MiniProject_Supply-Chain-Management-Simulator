import pytest

from src.orders import CustomerOrder, FULFILLED, OrderBook, PARTIAL, PENDING


def make_order(**overrides):
    fields = {"order_id": "CO-0001", "product_id": "P-001", "quantity": 10, "day": 1}
    fields.update(overrides)
    return CustomerOrder(**fields)


@pytest.mark.parametrize("overrides", [
    {"quantity": 0},
    {"quantity": -5},
    {"quantity": 2.5},
    {"quantity": True},
    {"order_id": " "},
    {"product_id": ""},
    {"day": -3},
    {"day": 1.5},
    {"fulfilled_qty": 50},
    {"fulfilled_qty": -1},
    {"status": "NONSENSE"},
    {"fulfilled_qty": 0, "status": FULFILLED},
    {"fulfilled_qty": 4, "status": PENDING},
])
def test_invalid_order_rejected(overrides):
    """TC-ORD-05: an order with invalid or inconsistent fields cannot be created."""
    with pytest.raises(ValueError):
        make_order(**overrides)


def test_new_order_pending():
    """TC-ORD-06: a new order is PENDING and nothing has been shipped."""
    order = make_order()
    assert order.status == PENDING
    assert order.fulfilled_qty == 0
    assert order.remaining == 10


def test_partial_shipment():
    """TC-ORD-07: order of 10, ship 4, status PARTIAL with 6 remaining."""
    order = make_order()
    order.apply_shipment(4)
    assert order.status == PARTIAL
    assert order.fulfilled_qty == 4
    assert order.remaining == 6


def test_full_shipment():
    """TC-ORD-08: order of 10, ship 4 then 6, status FULFILLED."""
    order = make_order()
    order.apply_shipment(4)
    order.apply_shipment(6)
    assert order.status == FULFILLED
    assert order.remaining == 0


@pytest.mark.parametrize("bad_qty", [11, 0, -2])
def test_overshipment_rejected(bad_qty):
    """TC-ORD-09: shipping more than remaining, zero or a negative amount is rejected and changes nothing."""
    order = make_order()
    with pytest.raises(ValueError):
        order.apply_shipment(bad_qty)
    assert order.fulfilled_qty == 0
    assert order.status == PENDING
def test_order_book_numbers_orders_in_sequence():
    """TC-ORD-10: create numbers orders CO-0001, CO-0002, ... and returns the new order."""
    book = OrderBook()
    first = book.create("P-001", 10, 1)
    second = book.create("P-002", 5, 1)
    assert first.order_id == "CO-0001"
    assert second.order_id == "CO-0002"
    assert first.status == PENDING
    with pytest.raises(ValueError):
        book.create("P-001", 0, 1)
    assert len(book.all_orders()) == 2
    assert book.create("P-003", 4, 1).order_id == "CO-0003"


def test_order_book_get_and_unknown_id():
    """TC-ORD-11: get returns the stored order; an unknown ID raises KeyError."""
    book = OrderBook()
    order = book.create("P-001", 10, 1)
    assert book.get("CO-0001") is order
    with pytest.raises(KeyError, match="CO-9999"):
        book.get("CO-9999")


def test_order_book_open_orders_excludes_fulfilled():
    """TC-ORD-12: open_orders lists unfulfilled orders oldest first and can filter by product."""
    book = OrderBook()
    a = book.create("P-001", 10, 1)
    b = book.create("P-002", 5, 1)
    c = book.create("P-001", 3, 2)
    b.apply_shipment(5)
    assert book.open_orders() == [a, c]
    assert book.open_orders("P-001") == [a, c]
    assert book.open_orders("P-002") == []


def test_order_book_all_orders_oldest_first():
    """TC-ORD-13: all_orders returns every order, fulfilled or not, oldest first."""
    book = OrderBook()
    assert book.all_orders() == []
    a = book.create("P-001", 10, 1)
    b = book.create("P-002", 5, 1)
    b.apply_shipment(5)
    assert book.all_orders() == [a, b]