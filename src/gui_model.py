"""Logic behind the desktop window (SCM-F-036).

Everything the window shows is computed here, so it can be tested without a
display. src/gui.py only lays out widgets and calls these functions.
"""
import glob
import os

from src.clock import EVENT_TYPES
from src.config_loader import load_config, validate_config
from src.simulation import SupplyChainSimulation

DEFAULT_CONFIG = os.path.join("data", "sample_config.json")
SCENARIO_GLOB = os.path.join("data", "scenarios", "*.json")
ALL_EVENTS = "All events"

# Label, key and kind for each KPI, in the order the CLI summary prints them.
KPI_ROWS = (
    ("Fill rate", "fill_rate", "percent"),
    ("Service level", "service_level", "percent"),
    ("Backorder units at end", "total_backorder_end", "count"),
    ("Average inventory units", "avg_inventory_units", "number"),
    ("Inventory turnover", "inventory_turnover", "number"),
    ("Forecast mean absolute error", "forecast_mae", "number"),
)
COST_ROWS = (
    ("Holding", "holding"),
    ("Stockout", "stockout"),
    ("Ordering", "ordering"),
    ("Purchase", "purchase"),
    ("Transport", "transport"),
    ("Total", "total"),
)


def list_scenarios(root: str = ".") -> list:
    """The sample config first, then every demo scenario, as paths relative to root."""
    paths = []
    if os.path.isfile(os.path.join(root, DEFAULT_CONFIG)):
        paths.append(DEFAULT_CONFIG)
    found = sorted(glob.glob(os.path.join(root, SCENARIO_GLOB)))
    paths.extend(os.path.relpath(path, root) for path in found)
    return paths


def parse_days(text) -> int | None:
    """Blank means "use the config"; otherwise a whole number of at least 1."""
    if text is None or not str(text).strip():
        return None
    value = str(text).strip()
    if not value.isdigit() or int(value) < 1:
        raise ValueError(f"days must be a whole number of at least 1, got {value!r}")
    return int(value)


def run_scenario(config_path: str, days=None):
    """Load and validate the scenario, apply a day override, and run it.

    Raises FileNotFoundError or ValueError with the same messages as the CLI.
    """
    config = load_config(config_path)
    if days is not None:
        config["simulation"]["days"] = days
        validate_config(config)
    return SupplyChainSimulation(config).run()


def _format(value, kind: str) -> str:
    if kind == "percent":
        return f"{value * 100:.2f}%"
    if kind == "count":
        return str(value)
    return f"{value:.2f}"


def kpi_rows(kpis: dict) -> list:
    """(label, display value) pairs for the KPI table."""
    return [(label, _format(kpis[key], kind)) for label, key, kind in KPI_ROWS]


def cost_rows(costs: dict) -> list:
    """(label, value in rupees) pairs for the cost table."""
    return [(label, f"{costs[key]:,.2f}") for label, key in COST_ROWS]


def event_counts(events) -> list:
    """(event type, count) for every event type, in EVENT_TYPES order."""
    return [(event_type, events.count(event_type)) for event_type in EVENT_TYPES]


def event_rows(events, event_type: str = ALL_EVENTS) -> list:
    """(day, type, message) rows, optionally for one event type only."""
    selected = events.events() if event_type == ALL_EVENTS else events.events(event_type)
    return [(event["day"], event["type"], event["message"]) for event in selected]


def stock_series(daily_records: list) -> dict:
    """End-of-day stock per product, ordered by day: {product_id: [stock, ...]}."""
    series = {}
    for record in sorted(daily_records, key=lambda r: (r["product_id"], r["day"])):
        series.setdefault(record["product_id"], []).append(record["stock_end"])
    return series


def chart_points(series: dict, width: int, height: int, margin: int = 40) -> dict:
    """Pixel coordinates for each product's line, inside a width x height area.

    Day 0 is at the left margin and the last day at the right margin; stock 0 is
    at the bottom margin and the highest stock in any series at the top margin.
    """
    if width <= 2 * margin or height <= 2 * margin:
        raise ValueError("chart area is too small for its margins")
    longest = max((len(values) for values in series.values()), default=0)
    highest = max((max(values) for values in series.values() if values), default=0)
    plot_w = width - 2 * margin
    plot_h = height - 2 * margin
    x_step = plot_w / (longest - 1) if longest > 1 else 0
    y_scale = plot_h / highest if highest else 0
    points = {}
    for product_id, values in series.items():
        points[product_id] = [
            (margin + day * x_step, height - margin - stock * y_scale)
            for day, stock in enumerate(values)
        ]
    return points


# Headline figures shown as coloured cards above the tables: title and key.
CARD_ROWS = (
    ("Fill rate", "fill_rate"),
    ("Service level", "service_level"),
    ("Total cost (Rs)", "total"),
    ("Delayed orders", "PO_DELAYED"),
    ("Stockout events", "STOCKOUT"),
)


def card_level(key: str, value) -> str:
    """Colour band for a headline figure: good, warn, bad or neutral.

    These are display thresholds for the window only, not requirements:
    rates of 98% or more are good and below 90% bad; any delayed order is a
    warning; any stockout is bad; cost has no band.
    """
    if key in ("fill_rate", "service_level"):
        if value >= 0.98:
            return "good"
        return "warn" if value >= 0.90 else "bad"
    if key == "PO_DELAYED":
        return "good" if value == 0 else "warn"
    if key == "STOCKOUT":
        return "good" if value == 0 else "bad"
    return "neutral"


def summary_cards(result) -> list:
    """(title, display value, level) for each headline card."""
    values = {
        "fill_rate": result.kpis["fill_rate"],
        "service_level": result.kpis["service_level"],
        "total": result.costs["total"],
        "PO_DELAYED": result.events.count("PO_DELAYED"),
        "STOCKOUT": result.events.count("STOCKOUT"),
    }
    cards = []
    for title, key in CARD_ROWS:
        value = values[key]
        if key in ("fill_rate", "service_level"):
            text = _format(value, "percent")
        elif key == "total":
            text = f"{value:,.2f}"
        else:
            text = str(value)
        cards.append((title, text, card_level(key, value)))
    return cards


def run_summary(config_path: str, result) -> str:
    """One status line describing the run."""
    days = len({record["day"] for record in result.daily_records})
    products = len({record["product_id"] for record in result.daily_records})
    return (f"{os.path.basename(config_path)}: {days} days, {products} products, "
            f"{len(result.daily_records)} daily records")
