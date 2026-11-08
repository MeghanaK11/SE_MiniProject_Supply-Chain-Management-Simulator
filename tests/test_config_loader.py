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
    ("supplier without prices", lambda cfg: cfg["suppliers"][0].update(prices={}), "prices"),
]


@pytest.mark.parametrize("label, mutate, expected", MALFORMED, ids=[m[0] for m in MALFORMED])
def test_missing_section(sample, label, mutate, expected):
    """TC-CFG-02: a missing, wrongly typed or malformed section raises ValueError naming it."""
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


@pytest.mark.parametrize("where", ["demand", "initial_stock", "supplier_prices", "transport_mode", "no_demand"])
def test_unknown_product_in_demand(sample, tmp_path, where):
    """TC-CFG-04: a reference to an unknown product or transport mode, or a product with no demand, is rejected."""
    if where == "demand":
        sample["demand"]["P-999"] = {"pattern": "constant", "base": 1}
        expected = "P-999"
    elif where == "initial_stock":
        sample["warehouse"]["initial_stock"]["P-999"] = 5
        expected = "P-999"
    elif where == "supplier_prices":
        sample["suppliers"][0]["prices"]["P-999"] = 10.0
        expected = "P-999"
    elif where == "transport_mode":
        sample["suppliers"][0]["transport_mode"] = "sea"
        expected = "sea"
    else:
        del sample["demand"]["P-003"]
        expected = "P-003"
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
