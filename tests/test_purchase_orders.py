import json
from pathlib import Path
 
import pytest
 
from src.purchase_orders import PLACED, create_purchase_order
from src.suppliers import Supplier
 
SAMPLE_CONFIG = Path(__file__).resolve().parent.parent / "data" / "sample_config.json"
 
 
def sample_supplier(supplier_id):
    """Build the real Supplier from the sample config, so module mismatches show up here."""
    with open(SAMPLE_CONFIG, encoding="utf-8") as f:
        entries = json.load(f)["suppliers"]
    return Supplier.from_dict(next(e for e in entries if e["supplier_id"] == supplier_id))
 
 
def test_po_delivery_day():
    """TC-PO-01: S-001 (3-day lead time), order day 5 gives delivery day 8."""
    po = create_purchase_order("PO-0001", sample_supplier("S-001"), "P-001", 100, 5)
    assert po.expected_delivery_day == 8
    assert po.order_day == 5
    assert po.status == PLACED
    assert (po.po_id, po.supplier_id, po.product_id, po.quantity) == ("PO-0001", "S-001", "P-001", 100)
 
 
def test_po_total_cost():
    """TC-PO-02: 100 units of P-001 from S-001 gives total_cost 11000.0."""
    po = create_purchase_order("PO-0001", sample_supplier("S-001"), "P-001", 100, 5)
    assert po.unit_price == 110.0
    assert po.total_cost == 11000.0
 
 
def test_po_over_capacity_rejected():
    """TC-PO-03: 201 units from S-002 (max 200) raises ValueError; exactly 200 is allowed."""
    s002 = sample_supplier("S-002")
    with pytest.raises(ValueError, match="quantity"):
        create_purchase_order("PO-0001", s002, "P-001", 201, 1)
    assert create_purchase_order("PO-0002", s002, "P-001", 200, 1).quantity == 200
 
 
def test_po_product_not_supplied():
    """TC-PO-04: P-003 from S-001 (not sold) raises ValueError, not KeyError."""
    with pytest.raises(ValueError, match="P-003"):
        create_purchase_order("PO-0001", sample_supplier("S-001"), "P-003", 10, 1)
 
 
@pytest.mark.parametrize("bad_qty", [0, -5, 2.5, True])
def test_po_zero_quantity(bad_qty):
    """TC-PO-05: 0 units, or a negative, fractional or bool quantity, raises ValueError; so does a blank po_id."""
    s001 = sample_supplier("S-001")
    with pytest.raises(ValueError, match="quantity"):
        create_purchase_order("PO-0001", s001, "P-001", bad_qty, 1)
    with pytest.raises(ValueError, match="po_id"):
        create_purchase_order("  ", s001, "P-001", 10, 1)
 