import pytest

import json
from pathlib import Path

from src.products import COST_FIELDS, Product, ProductCatalog

SAMPLE_CONFIG = Path(__file__).resolve().parent.parent / "data" / "sample_config.json"

P001 = {
    "product_id": "P-001",
    "name": "Packaged Drinking Water (case of 12)",
    "unit_cost": 120.0,
    "holding_cost_per_day": 0.5,
    "stockout_penalty": 30.0,
    "order_cost": 500.0,
}


def test_product_valid_creation():
    """TC-PRD-01: from_dict on the P-001 entry gives matching fields; extra keys are ignored."""
    product = Product.from_dict(P001)
    assert product.product_id == "P-001"
    assert product.name == "Packaged Drinking Water (case of 12)"
    assert product.unit_cost == 120.0
    assert product.holding_cost_per_day == 0.5
    assert product.stockout_penalty == 30.0
    assert product.order_cost == 500.0
    extra = Product.from_dict(dict(P001, notes="seasonal"))
    assert extra == product


@pytest.mark.parametrize("field", ["product_id", "name"])
def test_product_empty_id_rejected(field):
    """TC-PRD-02: an empty or blank product_id or name raises ValueError."""
    data = dict(P001, **{field: "  "})
    with pytest.raises(ValueError, match=field):
        Product.from_dict(data)


@pytest.mark.parametrize("field", COST_FIELDS)
@pytest.mark.parametrize("bad_value", [-1, "120", True, float("nan"), float("inf")])
def test_product_negative_cost_rejected(field, bad_value):
    """TC-PRD-03: a negative, non-numeric, NaN or infinite cost raises ValueError naming the field."""
    data = dict(P001, **{field: bad_value})
    with pytest.raises(ValueError, match=field):
        Product.from_dict(data)


def test_product_from_dict_missing_key():
    """TC-PRD-04: a dict without order_cost raises ValueError mentioning order_cost."""
    data = {k: v for k, v in P001.items() if k != "order_cost"}
    with pytest.raises(ValueError, match="order_cost"):
        Product.from_dict(data)


def make_product(product_id):
    return Product.from_dict(dict(P001, product_id=product_id))


def test_catalog_add_and_get():
    """TC-PRD-05: an added product comes back from get and the length grows."""
    catalog = ProductCatalog()
    product = make_product("P-001")
    catalog.add(product)
    assert catalog.get("P-001") is product
    assert len(catalog) == 1


def test_catalog_duplicate_rejected():
    """TC-PRD-06: adding the same product_id twice or a non-Product raises ValueError."""
    catalog = ProductCatalog()
    catalog.add(make_product("P-001"))
    with pytest.raises(ValueError, match="P-001"):
        catalog.add(make_product("P-001"))
    with pytest.raises(ValueError):
        catalog.add(P001)
    assert len(catalog) == 1


def test_catalog_unknown_id():
    """TC-PRD-07: get and remove of an unknown product_id raise KeyError."""
    catalog = ProductCatalog()
    with pytest.raises(KeyError):
        catalog.get("P-999")
    with pytest.raises(KeyError):
        catalog.remove("P-999")


def test_catalog_remove():
    """TC-PRD-08: after remove, the length drops by 1 and get raises KeyError."""
    catalog = ProductCatalog()
    catalog.add(make_product("P-001"))
    catalog.add(make_product("P-002"))
    catalog.remove("P-001")
    assert len(catalog) == 1
    with pytest.raises(KeyError):
        catalog.get("P-001")


def test_catalog_list_sorted():
    """TC-PRD-09: products added as P-003, P-001, P-002 are listed P-001, P-002, P-003."""
    catalog = ProductCatalog()
    for product_id in ["P-003", "P-001", "P-002"]:
        catalog.add(make_product(product_id))
    assert [p.product_id for p in catalog.list_all()] == ["P-001", "P-002", "P-003"]


def test_catalog_from_config():
    """TC-PRD-10: the sample scenario's products build a catalog of 3; malformed input is rejected."""
    config = json.loads(SAMPLE_CONFIG.read_text(encoding="utf-8"))
    catalog = ProductCatalog.from_config(config["products"])
    assert len(catalog) == 3
    assert catalog.get("P-002").unit_cost == 1400.0
    with pytest.raises(ValueError):
        ProductCatalog.from_config({"product_id": "P-001"})
    with pytest.raises(ValueError):
        ProductCatalog.from_config(["P-001"])
    with pytest.raises(ValueError):
        ProductCatalog.from_config([P001, P001])
