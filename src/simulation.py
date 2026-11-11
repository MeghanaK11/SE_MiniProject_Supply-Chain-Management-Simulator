
"""Simulation engine for the Supply Chain Management Simulator."""

from dataclasses import dataclass
import math
import random

from src.clock import EventLog, SimulationClock
from src.costs import CostTracker
from src.demand import DemandGenerator
from src.forecasting import (
    demand_std,
    exponential_smoothing,
    mean_absolute_error,
    moving_average,
)
from src.inventory import (
    economic_order_quantity,
    reorder_point,
    safety_stock,
    Warehouse,
)
from src.kpis import compute_kpis
from src.orders import OrderBook
from src.products import ProductCatalog
from src.purchase_orders import PurchaseOrderBook
from src.suppliers import SupplierRegistry, select_supplier


@dataclass
class SimulationResult:
    """Container for all outputs produced by a simulation run."""

    daily_records: list
    events: list
    kpis: dict
    costs: dict

    @property
    def cost_breakdown(self):
        """Return the cost breakdown."""
        return self.costs


VALID_FORECAST_METHODS = {
    "moving_average",
    "exponential_smoothing",
}


def apply_random_delay(reliability, rng, max_delay_days):
    """Return a random supplier delivery delay in days.

    A supplier delivers on time with the given reliability.
    Otherwise, a delay between 1 and max_delay_days is returned.
    """
    if (
        isinstance(reliability, bool)
        or not isinstance(reliability, (int, float))
        or not math.isfinite(reliability)
        or not 0 <= reliability <= 1
    ):
        raise ValueError("reliability must be between 0 and 1")

    if (
        isinstance(max_delay_days, bool)
        or not isinstance(max_delay_days, int)
        or max_delay_days < 1
    ):
        raise ValueError("max_delay_days must be a positive integer")

    if not hasattr(rng, "random") or not hasattr(rng, "randint"):
        raise ValueError("rng must provide random() and randint()")

    if rng.random() < reliability:
        return 0

    return rng.randint(1, max_delay_days)


def _forecast(history, method, window, alpha, fallback):
    """Calculate the next demand forecast."""
    if method not in VALID_FORECAST_METHODS:
        raise ValueError(f"Unknown forecast method: {method}")

    if not history:
        return float(fallback)

    if method == "exponential_smoothing":
        return exponential_smoothing(history, alpha)

    return moving_average(history, window)


def run_simulation(config):
    """
    Run a supply-chain simulation using a validated configuration.

    The function accepts the dictionary returned by load_config().
    """
    if not isinstance(config, dict):
        raise TypeError("config must be a dictionary")

    simulation_cfg = config["simulation"]
    policy = config["policy"]

    days = simulation_cfg["days"]
    rng = random.Random(simulation_cfg.get("seed", 42))

    forecast_method = policy.get("forecast_method", "moving_average")
    if forecast_method not in VALID_FORECAST_METHODS:
        raise ValueError(f"Unknown forecast method: {forecast_method}")

    forecast_window = policy.get("forecast_window", 7)
    smoothing_alpha = policy.get("smoothing_alpha", 0.3)
    service_z = policy.get("service_z", 1.65)
    supplier_strategy = policy.get("supplier_strategy", "balanced")
    max_delay = policy.get("max_supplier_delay_days", 3)

    products = ProductCatalog.from_config(config["products"])
    suppliers = SupplierRegistry.from_config(config["suppliers"])

    warehouse_cfg = config["warehouse"]
    warehouse = Warehouse(
        warehouse_id=warehouse_cfg["warehouse_id"],
        name=warehouse_cfg["name"],
        initial_stock=warehouse_cfg.get("initial_stock", {}),
    )

    demand_generators = {
        product_id: DemandGenerator.from_config(demand_cfg, rng)
        for product_id, demand_cfg in config["demand"].items()
    }

    order_book = OrderBook()
    po_book = PurchaseOrderBook()
    costs = CostTracker()
    clock = SimulationClock(days)
    event_log = EventLog()

    supplier_details = {
        item["supplier_id"]: item for item in config["suppliers"]
    }
    transport_modes = config["transport_modes"]

    histories = {
        product.product_id: []
        for product in products.list_all()
    }
    daily_records = []

    # Process days 0 through days - 1.
    while not clock.is_finished():
        day = clock.current_day

        # 1. Receive purchase orders that are due today.
        for po in po_book.due_on(day):
            warehouse.receive(po.product_id, po.quantity)
            po.advance("DELIVERED")

            event_log.record(
                day,
                "PO_RECEIVED",
                f"Purchase order {po.po_id} received: "
                f"{po.quantity} units of {po.product_id}",
            )

        # 2. Generate demand, fulfil orders, and record daily results.
        for product in products.list_all():
            product_id = product.product_id
            history = histories[product_id]

            demand_cfg = config["demand"][product_id]
            fallback = demand_cfg.get("base", 0)

            forecast = _forecast(
                history,
                forecast_method,
                forecast_window,
                smoothing_alpha,
                fallback,
            )

            demand = demand_generators[product_id].demand_for_day(day)
            history.append(demand)

            event_log.record(
                day,
                "DEMAND",
                f"Demand for {product_id}: {demand}",
            )

            if demand > 0:
                order_book.create(product_id, demand, day)

            available = warehouse.stock_level(product_id)
            allocated = order_book.allocate(product_id, available)

            shipped = (
                warehouse.ship(product_id, allocated)
                if allocated
                else 0
            )

            if shipped > 0:
                event_log.record(
                    day,
                    "SHIPMENT",
                    f"Shipped {shipped} units of {product_id}",
                )

            backorder = order_book.backorder_qty(product_id)

            if backorder > 0:
                event_log.record(
                    day,
                    "STOCKOUT",
                    f"Unfulfilled demand for {product_id}: {backorder}",
                )

            stock_end = warehouse.stock_level(product_id)
            on_order = po_book.on_order_qty(product_id)

            # 3. Record daily holding and stockout costs.
            costs.add_holding_cost(stock_end, product)
            costs.add_stockout_cost(backorder, product)

            daily_records.append({
                "day": day,
                "product_id": product_id,
                "demand": demand,
                "shipped": shipped,
                "stock_end": stock_end,
                "backorder": backorder,
                "on_order": on_order,
                "forecast": float(forecast),
            })

        # 4. Calculate reorder requirements after fulfilment.
        for product in products.list_all():
            product_id = product.product_id
            history = histories[product_id]

            forecast = _forecast(
                history,
                forecast_method,
                forecast_window,
                smoothing_alpha,
                config["demand"][product_id].get("base", 0),
            )

            sigma = demand_std(history, forecast_window)

            candidates = suppliers.suppliers_for(product_id)
            if not candidates:
                continue

            supplier = select_supplier(
                candidates,
                product_id,
                strategy=supplier_strategy,
            )

            lead_time = supplier.lead_time_days

            buffer_stock = safety_stock(
                service_z,
                sigma,
                lead_time,
            )

            rop = reorder_point(
                forecast,
                lead_time,
                buffer_stock,
            )

            on_order = po_book.on_order_qty(product_id)

            if not warehouse.needs_reorder(
                product_id,
                rop,
                on_order,
            ):
                continue

            # EOQ uses the forecast, annualized to 365 days.
            annual_demand = max(1, forecast * 365)
            annual_holding_cost = product.holding_cost_per_day * 365

            if annual_holding_cost > 0:
                quantity = economic_order_quantity(
                    annual_demand,
                    product.order_cost,
                    annual_holding_cost,
                )
            else:
                quantity = 1

            quantity = max(
                1,
                min(quantity, supplier.max_order_qty),
            )

            # place() creates the order directly in IN_TRANSIT.
            po = po_book.place(
                supplier,
                product_id,
                quantity,
                day,
            )

            # Apply supplier reliability delay.
            delay = apply_random_delay(
                supplier.reliability,
                rng,
                max_delay,
            )

            if delay > 0:
                po.expected_delivery_day += delay

                event_log.record(
                    day,
                    "PO_DELAYED",
                    f"Purchase order {po.po_id} delayed by {delay} days",
                )

            # Record ordering and purchase costs.
            costs.add_ordering_cost(product)
            costs.add_purchase_cost(quantity, po.unit_price)

            # Calculate transport cost using supplier configuration.
            raw_supplier = supplier_details[supplier.supplier_id]
            distance = raw_supplier.get("distance_km", 0)
            mode = raw_supplier.get("transport_mode")

            if mode in transport_modes:
                rate = transport_modes[mode]["cost_per_unit_km"]
                transport_cost = distance * quantity * rate
                costs.add_transport_cost(transport_cost)

            event_log.record(
                day,
                "PO_PLACED",
                f"Purchase order {po.po_id} placed for "
                f"{quantity} units of {product_id}",
            )

        # Advance only after the current day has been fully processed.
        clock.advance()

    # 5. Calculate forecast error and final KPIs.
    actual = [record["demand"] for record in daily_records]
    predicted = [record["forecast"] for record in daily_records]

    forecast_mae = (
        mean_absolute_error(actual, predicted)
        if actual else 0.0
    )

    kpis = compute_kpis(
        daily_records,
        products,
        forecast_mae=forecast_mae,
    )

    return SimulationResult(
        daily_records=daily_records,
        events=event_log.events(),
        kpis=kpis,
        costs=costs.breakdown(),
    )
