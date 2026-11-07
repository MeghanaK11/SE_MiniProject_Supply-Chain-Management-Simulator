"""Product data for the supply chain simulator (SCM-F-001).

The product catalog (SCM-F-002) is added to this module in a later backlog item.
"""
from dataclasses import dataclass

COST_FIELDS = ("unit_cost", "holding_cost_per_day", "stockout_penalty", "order_cost")
REQUIRED_KEYS = ("product_id", "name") + COST_FIELDS


@dataclass
class Product:
    """One product with its costs. All money values are in rupees."""

    product_id: str
    name: str
    unit_cost: float
    holding_cost_per_day: float
    stockout_penalty: float
    order_cost: float

    def __post_init__(self):
        for field in ("product_id", "name"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty string")
        for field in COST_FIELDS:
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{field} must be a number, got {value!r}")
            if value < 0:
                raise ValueError(f"{field} must be 0 or more, got {value!r}")

    @classmethod
    def from_dict(cls, data: dict) -> "Product":
        """Build a Product from one entry of the products list in the config."""
        for key in REQUIRED_KEYS:
            if key not in data:
                raise ValueError(f"product is missing required key '{key}'")
        return cls(**{key: data[key] for key in REQUIRED_KEYS})
