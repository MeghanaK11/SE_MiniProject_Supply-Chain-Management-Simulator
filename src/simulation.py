"""Simulation engine for the supply chain simulator (SCM-F-035).

Runs the warehouse day by day and returns the daily records, the event log,
the KPIs and the cost breakdown. Supplier delays and transport cost are not
included yet, so transport cost stays at 0.
"""
import random
from dataclasses import dataclass, field

from src.clock import EventLog, SimulationClock
from src.costs import CostTracker
from src.demand import DemandGenerator
from src.forecasting import demand_std, mean_absolute_error, moving_average
from src.inventory import (
    Warehouse,
    economic_order_quantity,
    reorder_point,
    safety_stock,
)
from src.kpis import compute_kpis
from src.orders import OrderBook
from src.products import ProductCatalog
from src.purchase_orders import DELIVERED, PurchaseOrderBook
from src.suppliers import SupplierRegistry, select_supplier

DAYS_PER_YEAR = 365


@dataclass
class SimulationResult:
    """What a run returns: daily records, the event log, the KPIs and the cost breakdown."""

    daily_records: list
    events: EventLog
    kpis: dict = field(default_factory=dict)
    costs: dict = field(default_factory=dict)


class SupplyChainSimulation:
    """Builds every domain component from a validated config and runs the daily loop."""

    def __init__(self, config: dict, days: int = None):
        self.config = config
        self.days = config["simulation"]["days"] if days is None else days
        self.policy = config["policy"]
        self.rng = random.Random(config["simulation"].get("seed", 0))

        self.catalog = ProductCatalog.from_config(config["products"])
        self.suppliers = SupplierRegistry.from_config(config["suppliers"])
        self.warehouse = Warehouse(
            config["warehouse"]["warehouse_id"],
            config["warehouse"]["name"],
            config["warehouse"].get("initial_stock", {}),
        )
        self.order_book = OrderBook()
        self.po_book = PurchaseOrderBook()
        self.clock = SimulationClock(self.days)
        self.log = EventLog()
        self.costs = CostTracker()

        self.product_ids = sorted(p.product_id for p in self.catalog.list_all())
        self.generators = {
            pid: DemandGenerator.from_config(config["demand"][pid], self.rng)
            for pid in self.product_ids
        }
        self.history = {pid: [] for pid in self.product_ids}
        self.daily_records = []
        self._last_forecast = {}
        self._forecast_actuals = []
        self._forecast_values = []

    def run(self) -> SimulationResult:
        """Run every day and return the result."""
        while not self.clock.is_finished():
            self._run_day(self.clock.current_day)
            self.clock.advance()
        mae = (mean_absolute_error(self._forecast_actuals, self._forecast_values)
               if self._forecast_actuals else 0.0)
        return SimulationResult(
            daily_records=self.daily_records,
            events=self.log,
            kpis=compute_kpis(self.daily_records, self.catalog.list_all(), mae),
            costs=self.costs.breakdown(),
        )

    def _run_day(self, day: int) -> None:
        self._receive_due_orders(day)
        for product_id in self.product_ids:
            demand = self._capture_demand(product_id, day)
            shipped = self._fulfil(product_id, day)
            forecast = self._forecast(product_id, demand)
            self._reorder(product_id, day, forecast)
            record = {
                "day": day,
                "product_id": product_id,
                "demand": demand,
                "shipped": shipped,
                "stock_end": self.warehouse.stock_level(product_id),
                "backorder": self.order_book.backorder_qty(product_id),
                "on_order": self.po_book.on_order_qty(product_id),
                "forecast": forecast,
            }
            self.daily_records.append(record)
            product = self.catalog.get(product_id)
            self.costs.add_holding_cost(record["stock_end"], product)
            self.costs.add_stockout_cost(record["backorder"], product)

    def _receive_due_orders(self, day: int) -> None:
        """Step 1: deliver every purchase order that is due."""
        for order in self.po_book.due_on(day):
            self.warehouse.receive(order.product_id, order.quantity)
            order.advance(DELIVERED)
            self.log.record(
                day, "PO_RECEIVED",
                f"{order.po_id} {order.product_id} {order.quantity} units received",
            )

    def _capture_demand(self, product_id: str, day: int) -> int:
        """Step 2: generate the day's demand and create a customer order."""
        demand = self.generators[product_id].demand_for_day(day)
        if demand > 0:
            order = self.order_book.create(product_id, demand, day)
            self.log.record(
                day, "DEMAND", f"{product_id} {demand} units, order {order.order_id}"
            )
        return demand

    def _fulfil(self, product_id: str, day: int) -> int:
        """Step 3: give stock to the oldest orders first and ship it."""
        available = self.warehouse.stock_level(product_id)
        shipped = self.order_book.allocate(product_id, available)
        if shipped > 0:
            self.warehouse.ship(product_id, shipped)
            self.log.record(day, "SHIPMENT", f"{product_id} {shipped} units shipped")
        backorder = self.order_book.backorder_qty(product_id)
        if backorder > 0:
            self.log.record(day, "STOCKOUT", f"{product_id} {backorder} units on backorder")
        return shipped

    def _forecast(self, product_id: str, demand: int) -> float:
        """Step 4: moving average of recent demand (exponential smoothing comes in v2)."""
        if product_id in self._last_forecast:
            self._forecast_actuals.append(demand)
            self._forecast_values.append(self._last_forecast[product_id])
        self.history[product_id].append(demand)
        forecast = float(moving_average(self.history[product_id], self.policy["forecast_window"]))
        self._last_forecast[product_id] = forecast
        return forecast

    def _reorder(self, product_id: str, day: int, forecast: float) -> None:
        """Step 5: pick a supplier and place an EOQ-sized order if stock is low."""
        supplier = select_supplier(
            self.suppliers.suppliers_for(product_id),
            product_id,
            self.policy["supplier_strategy"],
        )
        std = demand_std(self.history[product_id], self.policy["forecast_window"])
        safety = safety_stock(self.policy["service_z"], std, supplier.lead_time_days)
        point = reorder_point(forecast, supplier.lead_time_days, safety)
        on_order = self.po_book.on_order_qty(product_id)
        if not self.warehouse.needs_reorder(product_id, point, on_order):
            return
        product = self.catalog.get(product_id)
        eoq = economic_order_quantity(
            forecast * DAYS_PER_YEAR,
            product.order_cost,
            product.holding_cost_per_day * DAYS_PER_YEAR,
        )
        quantity = max(1, min(eoq, supplier.max_order_qty))
        order = self.po_book.place(supplier, product_id, quantity, day)
        self.costs.add_ordering_cost(product)
        self.costs.add_purchase_cost(quantity, order.unit_price)
        self.log.record(
            day, "PO_PLACED",
            f"{order.po_id} {supplier.supplier_id} {product_id} {quantity} units, "
            f"due day {order.expected_delivery_day}",
        )