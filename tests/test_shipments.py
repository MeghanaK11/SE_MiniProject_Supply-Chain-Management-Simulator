
import pytest

from src.shipments import Shipment, ShipmentLog


TRANSPORT_MODES = {
    "road": {"cost_per_unit_km": 0.02},
    "rail": {"cost_per_unit_km": 0.01},
}


def test_road_cost():
    shipment = Shipment(
        "SHP-001", "Supplier A", "Warehouse",
        350, "road", 100
    )
    assert shipment.cost(TRANSPORT_MODES) == 700.0


def test_unknown_mode():
    shipment = Shipment(
        "SHP-002", "Supplier A", "Warehouse",
        350, "sea", 100
    )
    with pytest.raises(ValueError):
        shipment.cost(TRANSPORT_MODES)


def test_invalid_distance():
    with pytest.raises(ValueError):
        Shipment(
            "SHP-003", "Supplier A", "Warehouse",
            0, "road", 100
        )


def test_log_total_and_count():
    log = ShipmentLog()

    road_shipment = Shipment(
        "SHP-004", "Supplier A", "Warehouse",
        350, "road", 100
    )
    rail_shipment = Shipment(
        "SHP-005", "Supplier B", "Warehouse",
        200, "rail", 50
    )

    log.add(road_shipment)
    log.add(rail_shipment)

    assert log.total_cost(TRANSPORT_MODES) == 800.0
    assert log.count_by_mode() == {"road": 1, "rail": 1}
