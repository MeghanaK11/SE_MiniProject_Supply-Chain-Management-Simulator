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
    late = book.create("P-003", 2, 3)
    early = book.create("P-003", 2, 1)
    assert book.open_orders("P-003") == [early, late]


def test_order_book_all_orders_oldest_first():
    """TC-ORD-13: all_orders returns every order, fulfilled or not, oldest first."""
    book = OrderBook()
    assert book.all_orders() == []
    a = book.create("P-001", 10, 1)
    b = book.create("P-002", 5, 1)
    b.apply_shipment(5)
    assert book.all_orders() == [a, b]


def test_allocate_serves_oldest_orders_first():
    """TC-ORD-14: orders of 5 (day 1) and 5 (day 2), allocate 7 fills the first and part of the second."""
    book = OrderBook()
    first = book.create("P-001", 5, 1)
    second = book.create("P-001", 5, 2)
    assert book.allocate("P-001", 7) == 7
    assert first.status == FULFILLED
    assert second.status == PARTIAL
    assert second.fulfilled_qty == 2
    assert book.backorder_qty("P-001") == 3
    # day order beats creation order: a day-3 order created first is served second
    other = OrderBook()
    late = other.create("P-001", 6, 3)
    early = other.create("P-001", 6, 1)
    assert other.allocate("P-001", 8) == 8
    assert early.status == FULFILLED
    assert late.fulfilled_qty == 2


def test_allocate_with_more_stock_than_demand():
    """TC-ORD-15: with enough stock every order is fulfilled and only the demand is allocated."""
    book = OrderBook()
    a = book.create("P-001", 4, 1)
    b = book.create("P-001", 3, 2)
    assert book.allocate("P-001", 100) == 7
    assert a.status == FULFILLED and b.status == FULFILLED
    assert book.open_orders("P-001") == []


def test_backorder_qty_sums_remaining_per_product():
    """TC-ORD-16: backorder_qty adds up units still owed for one product only."""
    book = OrderBook()
    book.create("P-001", 10, 1)
    book.create("P-001", 5, 2)
    book.create("P-002", 7, 1)
    assert book.backorder_qty("P-001") == 15
    book.allocate("P-001", 12)
    assert book.backorder_qty("P-001") == 3
    assert book.backorder_qty("P-002") == 7
    assert book.backorder_qty("P-999") == 0


@pytest.mark.parametrize("bad_qty", [-1, 2.5, True, None])
def test_allocate_rejects_bad_stock_and_zero_changes_nothing(bad_qty):
    """TC-ORD-17: invalid stock raises ValueError and changes nothing; zero stock allocates 0."""
    book = OrderBook()
    order = book.create("P-001", 5, 1)
    other = book.create("P-002", 5, 1)
    with pytest.raises(ValueError):
        book.allocate("P-001", bad_qty)
    assert order.fulfilled_qty == 0
    assert book.allocate("P-001", 0) == 0
    assert book.allocate("P-001", 5) == 5
    assert order.status == FULFILLED
    assert other.status == PENDING