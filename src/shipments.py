
"""Shipments and inbound transport costs (SCM-F-032)."""

import math
from dataclasses import dataclass


@dataclass
class Shipment:
    """Goods transported from a supplier to a warehouse."""

    shipment_id: str
    origin: str
    destination: str
    distance_km: float
    mode: str
    quantity: int

    def __post_init__(self):
        """Validate shipment distance and quantity."""
        if (
            isinstance(self.distance_km, bool)
            or not isinstance(self.distance_km, (int, float))
            or not math.isfinite(self.distance_km)
            or self.distance_km <= 0
        ):
            raise ValueError("distance_km must be greater than 0")

        if (
            isinstance(self.quantity, bool)
            or not isinstance(self.quantity, int)
            or self.quantity < 1
        ):
            raise ValueError("quantity must be an integer of at least 1")

    def cost(self, transport_modes: dict) -> float:
        """Calculate transport cost using distance, quantity and mode rate."""
        if not isinstance(transport_modes, dict) or self.mode not in transport_modes:
            raise ValueError(f"unknown transport mode: {self.mode}")

        mode_config = transport_modes[self.mode]

        if not isinstance(mode_config, dict) or "cost_per_unit_km" not in mode_config:
            raise ValueError(f"invalid transport configuration for {self.mode}")

        rate = mode_config["cost_per_unit_km"]

        if (
            isinstance(rate, bool)
            or not isinstance(rate, (int, float))
            or not math.isfinite(rate)
            or rate < 0
        ):
            raise ValueError("cost_per_unit_km must be a non-negative number")

        return self.distance_km * self.quantity * rate


class ShipmentLog:
    """Store shipments and calculate transport cost summaries."""

    def __init__(self):
        self.shipments = []

    def add(self, shipment: Shipment) -> None:
        """Add a shipment to the log."""
        if not isinstance(shipment, Shipment):
            raise ValueError("shipment must be a Shipment object")
        self.shipments.append(shipment)

    def total_cost(self, transport_modes: dict) -> float:
        """Return the total cost of all logged shipments."""
        return sum(
            shipment.cost(transport_modes)
            for shipment in self.shipments
        )

    def count_by_mode(self) -> dict:
        """Return the number of shipments for each transport mode."""
        counts = {}
        for shipment in self.shipments:
            counts[shipment.mode] = counts.get(shipment.mode, 0) + 1
        return counts
