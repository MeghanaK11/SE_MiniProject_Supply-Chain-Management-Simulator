import pytest

from src.products import COST_FIELDS, Product

P001 = {
    "product_id": "P-001",
    "name": "Packaged Drinking Water (case of 12)",
    "unit_cost": 120.0,
    "holding_cost_per_day": 0.5,
    "stockout_penalty": 30.0,
    "order_cost": 500.0,
}


def test_product_valid_creation():
    """TC-PRD-01: from_dict on the P-001 entry gives matching fields."""
    product = Product.from_dict(P001)
    assert product.product_id == "P-001"
    assert product.name == "Packaged Drinking Water (case of 12)"
    assert product.unit_cost == 120.0
    assert product.holding_cost_per_day == 0.5
    assert product.stockout_penalty == 30.0
    assert product.order_cost == 500.0


@pytest.mark.parametrize("field", ["product_id", "name"])
def test_product_empty_id_rejected(field):
    """TC-PRD-02: an empty or blank product_id or name raises ValueError."""
    data = dict(P001, **{field: "  "})
    with pytest.raises(ValueError, match=field):
        Product.from_dict(data)


@pytest.mark.parametrize("field", COST_FIELDS)
@pytest.mark.parametrize("bad_value", [-1, "120", True])
def test_product_negative_cost_rejected(field, bad_value):
    """TC-PRD-03: a negative or non-numeric cost raises ValueError naming the field."""
    data = dict(P001, **{field: bad_value})
    with pytest.raises(ValueError, match=field):
        Product.from_dict(data)


def test_product_from_dict_missing_key():
    """TC-PRD-04: a dict without order_cost raises ValueError mentioning order_cost."""
    data = {k: v for k, v in P001.items() if k != "order_cost"}
    with pytest.raises(ValueError, match="order_cost"):
        Product.from_dict(data)


def test_product_ignores_extra_keys():
    """TC-PRD-01: extra keys in the config entry do not stop the product being created."""
    product = Product.from_dict(dict(P001, notes="seasonal"))
    assert product.product_id == "P-001"
