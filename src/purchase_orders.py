class PurchaseOrder:
    """Represent a purchase order and manage its lifecycle."""

    VALID_STATUSES = {
        "PLACED",
        "IN_TRANSIT",
        "DELIVERED",
        "CANCELLED",
    }

    TRANSITIONS = {
        "PLACED": {"IN_TRANSIT", "CANCELLED"},
        "IN_TRANSIT": {"DELIVERED", "CANCELLED"},
        "DELIVERED": set(),
        "CANCELLED": set(),
    }

    def __init__(
        self,
        po_id,
        supplier,
        product_id,
        quantity,
        order_day,
        expected_delivery_day,
        status="PLACED",
    ):
        if not isinstance(po_id, str) or not po_id:
            raise ValueError("Purchase order ID is required")

        if not isinstance(product_id, str) or not product_id:
            raise ValueError("Product ID is required")

        if type(quantity) is not int or quantity <= 0:
            raise ValueError("Quantity must be a positive integer")

        if type(order_day) is not int or order_day < 0:
            raise ValueError("Order day must be non-negative")

        if (
            type(expected_delivery_day) is not int
            or expected_delivery_day < order_day
        ):
            raise ValueError("Invalid expected delivery day")

        if status not in self.VALID_STATUSES:
            raise ValueError("Invalid purchase order status")

        self.po_id = po_id
        self.supplier = supplier
        self.supplier_id = supplier.supplier_id
        self.product_id = product_id
        self.quantity = quantity
        self.order_day = order_day
        self.expected_delivery_day = expected_delivery_day
        self.status = status

    def advance(self, new_status):
        """Move the purchase order to a permitted next status."""
        if new_status not in self.VALID_STATUSES:
            raise ValueError("Unknown purchase order status")

        allowed = self.TRANSITIONS[self.status]

        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from {self.status} to {new_status}"
            )

        self.status = new_status


class PurchaseOrderBook:
    """Create and track purchase orders."""

    def __init__(self):
        self.orders = []
        self._next_id = 1

    def place(self, supplier, product_id, quantity, order_day):
        """Place a purchase order with a supplier."""

        if type(quantity) is not int or quantity <= 0:
            raise ValueError("Quantity must be a positive integer")

        if type(order_day) is not int or order_day < 0:
            raise ValueError("Order day must be non-negative")

        if quantity > supplier.max_order_qty:
            raise ValueError("Quantity exceeds supplier maximum order quantity")

        supplied_products = getattr(supplier, "products", None)

        if supplied_products is None:
            supplied_products = getattr(
                supplier, "product_ids", None
            )

        if supplied_products is None:
            supplied_products = getattr(
                supplier, "supplied_products", None
            )

        if supplied_products is not None and product_id not in supplied_products:
            raise ValueError("Supplier does not supply this product")

        expected_delivery_day = order_day + supplier.lead_time_days

        order = PurchaseOrder(
            po_id=f"PO-{self._next_id:04d}",
            supplier=supplier,
            product_id=product_id,
            quantity=quantity,
            order_day=order_day,
            expected_delivery_day=expected_delivery_day,
            status="IN_TRANSIT",
        )

        self.orders.append(order)
        self._next_id += 1

        return order

    def due_on(self, day):
        """Return open orders due on or before the given day."""
        if type(day) is not int or day < 0:
            raise ValueError("Day must be a non-negative integer")

        return sorted(
            [
                order for order in self.orders
                if order.status in ("PLACED", "IN_TRANSIT")
                and order.expected_delivery_day <= day
            ],
            key=lambda order: order.po_id,
        )

    def on_order_qty(self, product_id):
        """Return outstanding quantity for a product."""
        return sum(
            order.quantity
            for order in self.orders
            if order.product_id == product_id
            and order.status in ("PLACED", "IN_TRANSIT")
        )