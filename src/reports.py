"""CSV export and text summary (SCM-F-034, SCM-SR-003)."""
import csv
import os

COLUMNS = ("day", "product_id", "demand", "shipped", "stock_end", "backorder", "on_order", "forecast")
FORMULA_PREFIXES = ("=", "+", "-", "@")
SUMMARY_KPI_KEYS = ("fill_rate", "service_level", "avg_inventory_units",
                    "inventory_turnover", "total_backorder_end", "forecast_mae")
SUMMARY_COST_KEYS = ("holding", "stockout", "ordering", "purchase", "transport", "total")


def _safe_cell(value):
    """Prefix text that a spreadsheet could read as a formula with an apostrophe; leave numbers alone."""
    if isinstance(value, str) and value.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def export_daily_csv(daily_records: list, path: str) -> None:
    """Write one row per product per day to path, creating parent folders."""
    for index, record in enumerate(daily_records):
        for column in COLUMNS:
            if column not in record:
                raise ValueError(f"record {index} is missing column '{column}'")
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        for record in daily_records:
            writer.writerow([_safe_cell(record[column]) for column in COLUMNS])


def format_summary(kpis: dict, costs: dict) -> str:
    """Printable summary of costs (Rs, 2 decimals) and KPIs (rates in percent, 2 decimals)."""
    for key in SUMMARY_KPI_KEYS:
        if key not in kpis:
            raise ValueError(f"kpis is missing '{key}'")
    for key in SUMMARY_COST_KEYS:
        if key not in costs:
            raise ValueError(f"costs is missing '{key}'")
    lines = [
        "Costs (Rs)",
        f"  Holding cost: {costs['holding']:.2f}",
        f"  Stockout cost: {costs['stockout']:.2f}",
        f"  Ordering cost: {costs['ordering']:.2f}",
        f"  Purchase cost: {costs['purchase']:.2f}",
        f"  Transport cost: {costs['transport']:.2f}",
        f"  Total cost: {costs['total']:.2f}",
        "Service",
        f"  Fill rate: {kpis['fill_rate'] * 100:.2f}%",
        f"  Service level: {kpis['service_level'] * 100:.2f}%",
        f"  Backorder units at end: {kpis['total_backorder_end']}",
        "Inventory",
        f"  Average inventory units: {kpis['avg_inventory_units']:.2f}",
        f"  Inventory turnover: {kpis['inventory_turnover']:.2f}",
        "Forecast",
        f"  Mean absolute error: {kpis['forecast_mae']:.2f}",
    ]
    return "\n".join(lines)