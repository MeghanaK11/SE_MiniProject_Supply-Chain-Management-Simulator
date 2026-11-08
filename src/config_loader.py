"""Load and validate the scenario configuration (SCM-F-031, SCM-SR-001, SCM-SR-002).

This module checks that the file is safe to read, that every section is present
with the right shape, that the run length is in range, that every
cross-reference points at something that exists, and that initial stock, supplier
prices, demand entries and transport modes hold values of the right type and
range. Product and supplier fields such as costs, lead time and reliability are
checked again by Product and Supplier when the engine builds them.
"""
import json
import math
import os

REQUIRED_SECTIONS = ("simulation", "policy", "warehouse", "products",
                     "suppliers", "demand", "transport_modes")
MAX_CONFIG_BYTES = 1_000_000
MAX_DAYS = 3650
DEMAND_PATTERNS = ("constant", "uniform", "seasonal")

_SECTION_TYPES = {
    "simulation": dict, "policy": dict, "warehouse": dict, "products": list,
    "suppliers": list, "demand": dict, "transport_modes": dict,
}


def _is_int(value) -> bool:
    """True for real integers; bool is excluded on purpose."""
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value) -> bool:
    """True for finite ints and floats; bool, NaN and infinity are excluded."""
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def load_config(path: str) -> dict:
    """Read a JSON scenario file, validate it and return it as a dict."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"configuration file not found: {path}")
    size = os.path.getsize(path)
    if size > MAX_CONFIG_BYTES:
        raise ValueError(f"configuration file is {size} bytes; the limit is {MAX_CONFIG_BYTES}")
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    try:
        cfg = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}") from None
    validate_config(cfg)
    return cfg


def _ids(entries, key: str, section: str) -> list:
    """Collect the ID of every entry in a list section, rejecting gaps and duplicates."""
    ids = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"{section}[{index}] must be an object")
        value = entry.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{section}[{index}] is missing '{key}'")
        if value in ids:
            raise ValueError(f"duplicate {key} '{value}' in {section}")
        ids.append(value)
    return ids


def _check_demand_entry(product_id: str, entry) -> None:
    """One demand entry must name a known pattern and give whole, in-range parameters."""
    where = f"demand for '{product_id}'"
    if not isinstance(entry, dict):
        raise ValueError(f"{where} must be an object")
    pattern = entry.get("pattern")
    if not isinstance(pattern, str) or pattern not in DEMAND_PATTERNS:
        raise ValueError(f"{where} has pattern {pattern!r}; expected one of {DEMAND_PATTERNS}")
    if "base" not in entry:
        raise ValueError(f"{where} is missing 'base'")
    for key, minimum in (("base", 0), ("spread", 0), ("period", 1)):
        if key in entry:
            value = entry[key]
            if not _is_int(value) or value < minimum:
                raise ValueError(f"{where} has {key} {value!r}; it must be a whole number of at least {minimum}")
    if "amplitude" in entry and not _is_number(entry["amplitude"]):
        raise ValueError(f"{where} has amplitude {entry['amplitude']!r}; it must be a finite number")


def validate_config(cfg: dict) -> None:
    """Raise ValueError naming the first section or field that is missing, out of range or unknown."""
    if not isinstance(cfg, dict):
        raise ValueError("configuration must be a JSON object")
    for section in REQUIRED_SECTIONS:
        if section not in cfg:
            raise ValueError(f"missing required section '{section}'")
        if not isinstance(cfg[section], _SECTION_TYPES[section]):
            raise ValueError(f"section '{section}' must be a {_SECTION_TYPES[section].__name__}")

    days = cfg["simulation"].get("days")
    if not _is_int(days) or not 1 <= days <= MAX_DAYS:
        raise ValueError(f"simulation.days must be an integer from 1 to {MAX_DAYS}, got {days!r}")

    products = _ids(cfg["products"], "product_id", "products")
    if not products:
        raise ValueError("products must contain at least one product")
    suppliers = cfg["suppliers"]
    _ids(suppliers, "supplier_id", "suppliers")
    known = set(products)

    stock = cfg["warehouse"].get("initial_stock", {})
    if not isinstance(stock, dict):
        raise ValueError("warehouse.initial_stock must be an object")
    for product_id, quantity in stock.items():
        if product_id not in known:
            raise ValueError(f"warehouse.initial_stock refers to unknown product '{product_id}'")
        if not _is_int(quantity) or quantity < 0:
            raise ValueError(
                f"warehouse.initial_stock for '{product_id}' must be a whole number of 0 or more, got {quantity!r}")

    demand = cfg["demand"]
    for product_id, entry in demand.items():
        if product_id not in known:
            raise ValueError(f"demand refers to unknown product '{product_id}'")
        _check_demand_entry(product_id, entry)
    for product_id in products:
        if product_id not in demand:
            raise ValueError(f"product '{product_id}' has no demand entry")

    modes = cfg["transport_modes"]
    for name, mode_cfg in modes.items():
        rate = mode_cfg.get("cost_per_unit_km") if isinstance(mode_cfg, dict) else None
        if not _is_number(rate) or rate < 0:
            raise ValueError(f"transport_modes.{name}.cost_per_unit_km must be a number of 0 or more, got {rate!r}")

    sold = set()
    for supplier in suppliers:
        supplier_id = supplier["supplier_id"]
        prices = supplier.get("prices")
        if not isinstance(prices, dict) or not prices:
            raise ValueError(f"supplier '{supplier_id}' must have a non-empty prices object")
        for product_id, price in prices.items():
            if product_id not in known:
                raise ValueError(f"supplier '{supplier_id}' prices refer to unknown product '{product_id}'")
            if not _is_number(price) or price < 0:
                raise ValueError(
                    f"supplier '{supplier_id}' price for '{product_id}' must be a number of 0 or more, got {price!r}")
            sold.add(product_id)
        mode = supplier.get("transport_mode")
        if not isinstance(mode, str) or not mode.strip():
            raise ValueError(f"supplier '{supplier_id}' transport_mode must be a non-empty string, got {mode!r}")
        if mode not in modes:
            raise ValueError(f"supplier '{supplier_id}' uses unknown transport_mode {mode!r}")

    for product_id in products:
        if product_id not in sold:
            raise ValueError(f"product '{product_id}' is not sold by any supplier")
