import json

import pytest

from src.suppliers import Supplier, SupplierRegistry
 
S001 = {
    "supplier_id": "S-001",
    "name": "Deccan Wholesale Traders",
    "lead_time_days": 3,
    "prices": {"P-001": 110.0, "P-002": 1350.0},
    "reliability": 0.90,
    "max_order_qty": 500,
    "distance_km": 350,
    "transport_mode": "road",
}
 
 
def test_supplier_valid_creation():
    """TC-SUP-01: from_dict on the S-001 entry gives matching fields; extra keys are ignored."""
    supplier = Supplier.from_dict(S001)
    assert supplier.supplier_id == "S-001"
    assert supplier.name == "Deccan Wholesale Traders"
    assert supplier.lead_time_days == 3
    assert supplier.prices == {"P-001": 110.0, "P-002": 1350.0}
    assert supplier.reliability == 0.90
    assert supplier.max_order_qty == 500
    assert not hasattr(supplier, "distance_km")
    assert not hasattr(supplier, "transport_mode")
    direct = Supplier("S-001", "Deccan Wholesale Traders", 3,
                      {"P-001": 110.0, "P-002": 1350.0}, 0.90, 500)
    assert direct == supplier
    assert Supplier("S-009", "Free Sample Co", 1, {"P-001": 0}, 1.0, 10).price_for("P-001") == 0
 
 
@pytest.mark.parametrize("bad_value", [0, -1, 2.5, True, "3"])
def test_supplier_invalid_lead_time_rejected(bad_value):
    """TC-SUP-02: a lead time that is not a whole number of at least 1 raises ValueError."""
    with pytest.raises(ValueError, match="lead_time_days"):
        Supplier.from_dict(dict(S001, lead_time_days=bad_value))
 
 
@pytest.mark.parametrize("bad_value", [-0.1, 1.5, True, "0.9", float("nan")])
def test_supplier_invalid_reliability_rejected(bad_value):
    """TC-SUP-03: a reliability outside 0 to 1 or not a number raises ValueError."""
    with pytest.raises(ValueError, match="reliability"):
        Supplier.from_dict(dict(S001, reliability=bad_value))
 
 
BAD_FIELDS = [
    ("prices", {}),
    ("prices", {"P-001": -5.0}),
    ("prices", {"P-001": "110"}),
    ("prices", {"P-001": float("inf")}),
    ("prices", ["P-001", 110.0]),
    ("max_order_qty", 0),
    ("max_order_qty", 10.5),
    ("max_order_qty", True),
    ("supplier_id", "  "),
    ("name", ""),
]
 
 
def test_supplier_invalid_prices_or_capacity_rejected():
    """TC-SUP-04: bad prices, capacity, blank text or a missing key raise ValueError naming the field."""
    for field, bad_value in BAD_FIELDS:
        with pytest.raises(ValueError, match=field):
            Supplier.from_dict(dict(S001, **{field: bad_value}))
    missing = {k: v for k, v in S001.items() if k != "max_order_qty"}
    with pytest.raises(ValueError, match="max_order_qty"):
        Supplier.from_dict(missing)
 
 
def test_supplier_supplies_and_price_for():
    """TC-SUP-05: supplies and price_for answer for sold products; an unsold product raises KeyError."""
    supplier = Supplier.from_dict(S001)
    assert supplier.supplies("P-001") is True
    assert supplier.supplies("P-003") is False
    assert supplier.price_for("P-002") == 1350.0
    with pytest.raises(KeyError, match="P-003"):
        supplier.price_for("P-003")


def sample_config():
    with open("data/sample_config.json", encoding="utf-8") as f:
        return json.load(f)


def test_registry_add_and_get():
    """TC-SUP-06: a supplier that was added can be fetched by its ID."""
    registry = SupplierRegistry()
    supplier = Supplier.from_dict(S001)
    registry.add(supplier)
    assert registry.get("S-001") is supplier


def test_registry_duplicate_id_rejected():
    """TC-SUP-07: adding a second supplier with the same ID raises ValueError."""
    registry = SupplierRegistry()
    registry.add(Supplier.from_dict(S001))
    with pytest.raises(ValueError, match="S-001"):
        registry.add(Supplier.from_dict(dict(S001, name="Another Trader")))


def test_registry_unknown_id_rejected():
    """TC-SUP-08: get with an unknown supplier ID raises KeyError."""
    registry = SupplierRegistry()
    with pytest.raises(KeyError, match="S-999"):
        registry.get("S-999")


def test_registry_from_config_and_suppliers_for():
    """TC-SUP-09: from_config loads the sample suppliers; suppliers_for lists who sells each product."""
    registry = SupplierRegistry.from_config(sample_config())
    assert [s.supplier_id for s in registry.suppliers_for("P-001")] == ["S-001", "S-002"]
    assert [s.supplier_id for s in registry.suppliers_for("P-002")] == ["S-001", "S-003"]
    assert [s.supplier_id for s in registry.suppliers_for("P-003")] == ["S-002", "S-003"]
    assert registry.suppliers_for("P-999") == []