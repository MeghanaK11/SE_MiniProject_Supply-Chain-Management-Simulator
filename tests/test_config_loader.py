import copy
import json
from pathlib import Path

import pytest

from src.config_loader import MAX_CONFIG_BYTES, REQUIRED_SECTIONS, load_config, validate_config

SAMPLE_CONFIG = Path(__file__).resolve().parent.parent / "data" / "sample_config.json"


@pytest.fixture
def sample():
    return json.loads(SAMPLE_CONFIG.read_text(encoding="utf-8"))


def write(tmp_path, cfg):
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return str(path)


def test_load_sample_config():
    """TC-CFG-01: data/sample_config.json loads without error and keeps its values."""
    cfg = load_config(str(SAMPLE_CONFIG))
    assert cfg["simulation"]["days"] == 30
    assert len(cfg["products"]) == 3
    assert len(cfg["suppliers"]) == 3


def _drop(section):
    def mutate(cfg):
        del cfg[section]
    return mutate


def _set(section, value):
    def mutate(cfg):
        cfg[section] = value
    return mutate


def _duplicate_first(section):
    def mutate(cfg):
        cfg[section].append(copy.deepcopy(cfg[section][0]))
    return mutate


def _stock(value):
    def mutate(cfg):
        cfg["warehouse"]["initial_stock"]["P-001"] = value
    return mutate


def _price(value):
    def mutate(cfg):
        cfg["suppliers"][0]["prices"]["P-001"] = value
    return mutate


def _demand(**changes):
    """Change the P-001 demand entry; a value of None removes that key."""
    def mutate(cfg):
        entry = cfg["demand"]["P-001"]
        for key, value in changes.items():
            if value is None:
                entry.pop(key, None)
            else:
                entry[key] = value
    return mutate


def _demand_entry(value):
    def mutate(cfg):
        cfg["demand"]["P-001"] = value
    return mutate


def _mode_rate(value):
    def mutate(cfg):
        cfg["transport_modes"]["road"] = value
    return mutate


MALFORMED = [
    *[(f"missing {s}", _drop(s), s) for s in REQUIRED_SECTIONS],
    ("products not a list", _set("products", {"P-001": {}}), "products"),
    ("demand not an object", _set("demand", []), "demand"),
    ("no products", _set("products", []), "products"),
    ("product entry not an object", _set("products", ["P-001"]), "products"),
    ("product without id", _set("products", [{"name": "No ID"}]), "product_id"),
    ("duplicate product", _duplicate_first("products"), "duplicate product_id"),
    ("duplicate supplier", _duplicate_first("suppliers"), "duplicate supplier_id"),
    ("initial_stock not an object", lambda cfg: cfg["warehouse"].update(initial_stock=["P-001"]), "initial_stock"),
    ("initial_stock negative", _stock(-5), "initial_stock"),
    ("initial_stock fraction", _stock(2.5), "initial_stock"),
    ("initial_stock bool", _stock(True), "initial_stock"),
    ("initial_stock text", _stock("120"), "initial_stock"),
    ("initial_stock list", _stock([120]), "initial_stock"),
    ("supplier without prices", lambda cfg: cfg["suppliers"][0].update(prices={}), "prices"),
    ("supplier prices a list", lambda cfg: cfg["suppliers"][0].update(prices=["P-001", 110.0]), "prices"),
    ("price negative", _price(-1.0), "price for 'P-001'"),
    ("price text", _price("110"), "price for 'P-001'"),
    ("price bool", _price(True), "price for 'P-001'"),
    ("price NaN", _price(float("nan")), "price for 'P-001'"),
    ("price infinite", _price(float("inf")), "price for 'P-001'"),
    ("price object", _price({"amount": 110}), "price for 'P-001'"),
    ("demand entry not an object", _demand_entry(20), "demand for 'P-001'"),
    ("demand entry a list", _demand_entry(["uniform", 20]), "demand for 'P-001'"),
    ("demand without pattern", _demand(pattern=None), "pattern"),
    ("demand unknown pattern", _demand(pattern="random"), "pattern"),
    ("demand pattern a list", _demand(pattern=["uniform"]), "pattern"),
    ("demand without base", _demand(base=None), "base"),
    ("demand base negative", _demand(base=-1), "base"),
    ("demand base fraction", _demand(base=2.5), "base"),
    ("demand base text", _demand(base="20"), "base"),
    ("demand spread negative", _demand(spread=-1), "spread"),
    ("demand spread bool", _demand(spread=True), "spread"),
    ("demand period zero", _demand(pattern="seasonal", period=0), "period"),
    ("demand amplitude text", _demand(pattern="seasonal", amplitude="3"), "amplitude"),
    ("demand amplitude infinite", _demand(pattern="seasonal", amplitude=float("inf")), "amplitude"),
    ("transport mode not an object", _mode_rate(0.02), "cost_per_unit_km"),
    ("transport mode without rate", _mode_rate({}), "cost_per_unit_km"),
    ("transport mode rate negative", _mode_rate({"cost_per_unit_km": -0.01}), "cost_per_unit_km"),
    ("transport mode rate text", _mode_rate({"cost_per_unit_km": "0.02"}), "cost_per_unit_km"),
]


@pytest.mark.parametrize("label, mutate, expected", MALFORMED, ids=[m[0] for m in MALFORMED])
def test_missing_section(sample, label, mutate, expected):
    """TC-CFG-02: a missing, wrongly typed or malformed section or value raises ValueError naming it."""
    cfg = copy.deepcopy(sample)
    mutate(cfg)
    with pytest.raises(ValueError, match=expected):
        validate_config(cfg)
    with pytest.raises(ValueError, match="JSON object"):
        validate_config(["not", "an", "object"])


def test_invalid_json(tmp_path):
    """TC-CFG-03: malformed JSON raises ValueError and a missing file raises FileNotFoundError."""
    path = tmp_path / "broken.json"
    path.write_text("{bad", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        load_config(str(path))
    with pytest.raises(FileNotFoundError):
        load_config(str(tmp_path / "missing.json"))


BAD_REFERENCES = [
    ("demand", lambda cfg: cfg["demand"].update({"P-999": {"pattern": "constant", "base": 1}}), "P-999"),
    ("initial_stock", lambda cfg: cfg["warehouse"]["initial_stock"].update({"P-999": 5}), "P-999"),
    ("supplier_prices", lambda cfg: cfg["suppliers"][0]["prices"].update({"P-999": 10.0}), "P-999"),
    ("no_demand", lambda cfg: cfg["demand"].pop("P-003"), "P-003"),
    ("transport_mode unknown", lambda cfg: cfg["suppliers"][0].update(transport_mode="sea"), "sea"),
    ("transport_mode list", lambda cfg: cfg["suppliers"][0].update(transport_mode=["road"]), "transport_mode"),
    ("transport_mode integer", lambda cfg: cfg["suppliers"][0].update(transport_mode=1), "transport_mode"),
    ("transport_mode object", lambda cfg: cfg["suppliers"][0].update(transport_mode={"road": 1}), "transport_mode"),
    ("transport_mode null", lambda cfg: cfg["suppliers"][0].update(transport_mode=None), "transport_mode"),
    ("transport_mode blank", lambda cfg: cfg["suppliers"][0].update(transport_mode=" "), "transport_mode"),
    ("transport_mode missing", lambda cfg: cfg["suppliers"][0].pop("transport_mode"), "transport_mode"),
]


@pytest.mark.parametrize("label, mutate, expected", BAD_REFERENCES, ids=[b[0] for b in BAD_REFERENCES])
def test_unknown_product_in_demand(sample, tmp_path, label, mutate, expected):
    """TC-CFG-04: a reference to an unknown product, a transport mode that is unknown, missing or not a string, or a product with no demand, raises ValueError."""
    mutate(sample)
    with pytest.raises(ValueError, match=expected):
        load_config(write(tmp_path, sample))


def test_product_without_supplier(sample, tmp_path):
    """TC-CFG-05: a product that no supplier sells is rejected."""
    for supplier in sample["suppliers"]:
        supplier["prices"].pop("P-003", None)
    with pytest.raises(ValueError, match="P-003"):
        load_config(write(tmp_path, sample))


def test_days_out_of_range(sample, tmp_path):
    """TC-CFG-06: days outside 1 to 3650 or not an integer, and a file over 1 MB, are rejected; 1 and 3650 are accepted."""
    for days in (0, 5000, -1, "30", True, 2.5, None):
        sample["simulation"]["days"] = days
        with pytest.raises(ValueError, match="days"):
            load_config(write(tmp_path, sample))
    for days in (1, 3650):
        sample["simulation"]["days"] = days
        assert load_config(write(tmp_path, sample))["simulation"]["days"] == days
    big = tmp_path / "big.json"
    big.write_text(" " * (MAX_CONFIG_BYTES + 100_000) + "{}", encoding="utf-8")
    with pytest.raises(ValueError, match="limit"):
        load_config(str(big))
