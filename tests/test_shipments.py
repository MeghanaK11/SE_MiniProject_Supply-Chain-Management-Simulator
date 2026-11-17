"""Unit tests for shipments and inbound transport cost (SCM-F-032)."""
import pytest

from src.shipments import Shipment, ShipmentLog

TRANSPORT_MODES = {
    "road": {"cost_per_unit_km": 0.02},
    "rail": {"cost_per_unit_km": 0.01},
}


def make(shipment_id="SHP-001", distance_km=350, mode="road", quantity=100):
    return Shipment(shipment_id, "Supplier A", "Warehouse", distance_km, mode, quantity)


def test_road_cost():
    """TC-SHP-01: 350 km, 100 units by road at 0.02 per unit-km costs Rs 700.0."""
    assert make().cost(TRANSPORT_MODES) == pytest.approx(700.0)


def test_unknown_mode():
    """TC-SHP-02: a mode missing from transport_modes, or a broken mode entry, raises ValueError."""
    with pytest.raises(ValueError, match="unknown transport mode: sea"):
        make(mode="sea").cost(TRANSPORT_MODES)
    with pytest.raises(ValueError, match="unknown transport mode"):
        make().cost(None)
    with pytest.raises(ValueError, match="invalid transport configuration"):
        make().cost({"road": 0.02})
    for rate in (-0.01, float("nan"), True, "0.02"):
        with pytest.raises(ValueError, match="cost_per_unit_km"):
            make().cost({"road": {"cost_per_unit_km": rate}})


def test_invalid_distance():
    """TC-SHP-03: distance must be a finite number above 0 and quantity a whole number of at least 1."""
    for distance in (0, -5, float("inf"), True, "350"):
        with pytest.raises(ValueError, match="distance_km"):
            make(distance_km=distance)
    for quantity in (0, -1, 2.5, True):
        with pytest.raises(ValueError, match="quantity"):
            make(quantity=quantity)


def test_log_total_and_count():
    """TC-SHP-04: one road and one rail shipment give the summed cost and one of each mode; only Shipment objects are accepted."""
    log = ShipmentLog()
    assert log.total_cost(TRANSPORT_MODES) == 0
    assert log.count_by_mode() == {}
    log.add(make("SHP-004", 350, "road", 100))
    log.add(make("SHP-005", 200, "rail", 50))
    assert log.total_cost(TRANSPORT_MODES) == pytest.approx(800.0)
    assert log.count_by_mode() == {"road": 1, "rail": 1}
    with pytest.raises(ValueError, match="Shipment"):
        log.add({"shipment_id": "SHP-006"})
