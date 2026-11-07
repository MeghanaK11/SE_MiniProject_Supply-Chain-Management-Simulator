import pytest

from src.orders import CustomerOrder, FULFILLED, PARTIAL, PENDING


def make_order(quantity=10):
    return CustomerOrder(order_id="CO-0001", product_id="P-001", quantity=quantity, day=1)


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
def test_invalid_shipment_rejected(bad_qty):
    """TC-ORD-09: shipping more than remaining, zero or a negative amount is rejected."""
    order = make_order()
    with pytest.raises(ValueError):
        order.apply_shipment(bad_qty)
    assert order.fulfilled_qty == 0
    assert order.status == PENDING


@pytest.mark.parametrize("bad_quantity", [0, -5, 2.5, True])
def test_invalid_order_quantity_rejected(bad_quantity):
    """TC-ORD-09: an order quantity below 1 or not a whole number is rejected."""
    with pytest.raises(ValueError):
        make_order(quantity=bad_quantity)
