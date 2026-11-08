"""Load and validate the scenario configuration (SCM-F-031, SCM-SR-001, SCM-SR-002).

Field-level rules for products, suppliers and demand patterns are enforced by
their own classes when the engine builds them. This module checks that the file
is safe to read, that every section is present with the right shape, that the
run length is in range, and that every cross-reference points at something that
exists.
"""
import json
import os

REQUIRED_SECTIONS = ("simulation", "policy", "warehouse", "products",
                     "suppliers", "demand", "transport_modes")
MAX_CONFIG_BYTES = 1_000_000
MAX_DAYS = 3650

_SECTION_TYPES = {
    "simulation": dict, "policy": dict, "warehouse": dict, "products": list,
    "suppliers": list, "demand": dict, "transport_modes": dict,
}


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
    if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= MAX_DAYS:
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
    for product_id in stock:
        if product_id not in known:
            raise ValueError(f"warehouse.initial_stock refers to unknown product '{product_id}'")

    for product_id in cfg["demand"]:
        if product_id not in known:
            raise ValueError(f"demand refers to unknown product '{product_id}'")
    for product_id in products:
        if product_id not in cfg["demand"]:
            raise ValueError(f"product '{product_id}' has no demand entry")

    modes = cfg["transport_modes"]
    sold = set()
    for supplier in suppliers:
        supplier_id = supplier["supplier_id"]
        prices = supplier.get("prices")
        if not isinstance(prices, dict) or not prices:
            raise ValueError(f"supplier '{supplier_id}' must have a non-empty prices object")
        for product_id in prices:
            if product_id not in known:
                raise ValueError(f"supplier '{supplier_id}' prices refer to unknown product '{product_id}'")
            sold.add(product_id)
        mode = supplier.get("transport_mode")
        if mode not in modes:
            raise ValueError(f"supplier '{supplier_id}' uses unknown transport_mode {mode!r}")

    for product_id in products:
        if product_id not in sold:
            raise ValueError(f"product '{product_id}' is not sold by any supplier")
