class Warehouse:
    """Tracks stock levels for products in a warehouse."""

    def __init__(self, warehouse_id, name, initial_stock):
        if any(qty < 0 for qty in initial_stock.values()):
            raise ValueError("Initial stock cannot be negative")

        self.warehouse_id = warehouse_id
        self.name = name
        self._stock = dict(initial_stock)

    def receive(self, product_id, qty):
        if qty <= 0:
            raise ValueError("Quantity must be positive")

        self._stock[product_id] = self._stock.get(product_id, 0) + qty

    def ship(self, product_id, qty):
        if qty <= 0:
            raise ValueError("Quantity must be positive")

        available = self.stock_level(product_id)
        shipped = min(qty, available)
        self._stock[product_id] = available - shipped

        return shipped

    def stock_level(self, product_id):
        return self._stock.get(product_id, 0)

    def snapshot(self):
        return dict(self._stock)