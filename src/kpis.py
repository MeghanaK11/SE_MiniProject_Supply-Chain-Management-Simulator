
"""KPI calculations for the supply chain simulator (SCM-F-033)."""

import math
from collections.abc import Mapping


DAILY_RECORD_FIELDS = (
    "day",
    "product_id",
    "demand",
    "shipped",
    "stock_end",
    "backorder",
    "on_order",
    "forecast",
)


def _validate_records(daily_records):
    """Validate the daily simulation records."""
    if not isinstance(daily_records, (list, tuple)):
        raise ValueError("daily_records must be a list or tuple")

    for index, record in enumerate(daily_records):
        if not isinstance(record, Mapping):
            raise ValueError(f"record {index} must be a dictionary")

        for field in DAILY_RECORD_FIELDS:
            if field not in record:
                raise ValueError(
                    f"record {index} is missing required field '{field}'"
                )

        for field in (
            "day", "demand", "shipped",
            "stock_end", "backorder", "on_order",
        ):
            value = record[field]
            if type(value) is not int or value < 0:
                raise ValueError(
                    f"record {index}: {field} must be a non-negative integer"
                )

        product_id = record["product_id"]
        if not isinstance(product_id, str) or not product_id.strip():
            raise ValueError(
                f"record {index}: product_id must be a non-empty string"
            )

        forecast = record["forecast"]
        if (
            isinstance(forecast, bool)
            or not isinstance(forecast, (int, float))
            or not math.isfinite(forecast)
            or forecast < 0
        ):
            raise ValueError(
                f"record {index}: forecast must be a finite non-negative number"
            )


def _product_map(products):
    """Convert supported product collections into an ID-to-product mapping."""
    if hasattr(products, "list_all"):
        products = products.list_all()

    if isinstance(products, Mapping):
        result = dict(products)
    elif isinstance(products, (list, tuple)):
        result = {
            product.product_id: product
            for product in products
        }
    else:
        raise ValueError(
            "products must be a ProductCatalog, mapping, list or tuple"
        )

    for product_id, product in result.items():
        if not hasattr(product, "unit_cost"):
            raise ValueError(
                f"product '{product_id}' must have a unit_cost"
            )

        cost = product.unit_cost
        if (
            isinstance(cost, bool)
            or not isinstance(cost, (int, float))
            or not math.isfinite(cost)
            or cost < 0
        ):
            raise ValueError(
                f"product '{product_id}' has an invalid unit_cost"
            )

    return result


def fill_rate(total_shipped, total_demand):
    """Return total shipped divided by total demand."""
    for name, value in (
        ("total_shipped", total_shipped),
        ("total_demand", total_demand),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(f"{name} must be a finite non-negative number")

    if total_shipped > total_demand:
        raise ValueError("total_shipped cannot exceed total_demand")

    if total_demand == 0:
        return 1.0

    return round(total_shipped / total_demand, 4)


def service_level(daily_records):
    """Return the proportion of product-days without a backorder."""
    if not daily_records:
        return 0.0

    days_with_stockout = sum(
        record["backorder"] > 0
        for record in daily_records
    )

    return round(1.0 - days_with_stockout / len(daily_records), 4)


def average_inventory_units(daily_records):
    """Return average ending inventory across all product-days."""
    if not daily_records:
        return 0.0

    total_stock = sum(
        record["stock_end"]
        for record in daily_records
    )

    return round(total_stock / len(daily_records), 4)


def inventory_turnover(daily_records, products):
    """Return COGS divided by average inventory value per distinct day."""
    if not daily_records:
        return 0.0

    product_lookup = _product_map(products)

    total_cogs = 0.0
    total_inventory_value = 0.0

    for record in daily_records:
        product_id = record["product_id"]

        if product_id not in product_lookup:
            raise ValueError(
                f"unknown product_id '{product_id}' in daily records"
            )

        unit_cost = product_lookup[product_id].unit_cost

        total_cogs += record["shipped"] * unit_cost
        total_inventory_value += record["stock_end"] * unit_cost

    distinct_days = len({record["day"] for record in daily_records})
    average_inventory_value = total_inventory_value / distinct_days

    if average_inventory_value == 0:
        return 0.0

    return round(total_cogs / average_inventory_value, 4)


def compute_kpis(daily_records, products, forecast_mae=0.0):
    """
    Compute the KPIs for a complete simulation run.

    Returns fill rate, service level, average inventory units,
    inventory turnover and total ending backorders.
    """
    _validate_records(daily_records)

    if (
        isinstance(forecast_mae, bool)
        or not isinstance(forecast_mae, (int, float))
        or not math.isfinite(forecast_mae)
        or forecast_mae < 0
    ):
        raise ValueError(
            "forecast_mae must be a finite non-negative number"
        )

    if not daily_records:
        return {
            "fill_rate": 1.0,
            "service_level": 0.0,
            "avg_inventory_units": 0.0,
            "inventory_turnover": 0.0,
            "total_backorder_end": 0,
            "forecast_mae": round(float(forecast_mae), 4),
        }

    total_demand = sum(
        record["demand"]
        for record in daily_records
    )

    total_shipped = sum(
        record["shipped"]
        for record in daily_records
    )

    # Find the latest recorded day for each product.
    latest_records = {}

    for record in daily_records:
        product_id = record["product_id"]

        if (
            product_id not in latest_records
            or record["day"] > latest_records[product_id]["day"]
        ):
            latest_records[product_id] = record

    total_backorder_end = sum(
        record["backorder"]
        for record in latest_records.values()
    )

    return {
        "fill_rate": fill_rate(total_shipped, total_demand),
        "service_level": service_level(daily_records),
        "avg_inventory_units": average_inventory_units(daily_records),
        "inventory_turnover": inventory_turnover(
            daily_records, products
        ),
        "total_backorder_end": total_backorder_end,
        "forecast_mae": round(float(forecast_mae), 4),
    }
