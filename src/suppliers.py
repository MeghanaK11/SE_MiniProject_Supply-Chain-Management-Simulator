"""Suppliers for the supply chain simulator (SCM-F-010).
 
The supplier registry (SCM-F-011) and supplier selection (SCM-F-012) are added
to this module in later backlog items.
"""
import math
from dataclasses import dataclass
 
REQUIRED_KEYS = (
    "supplier_id",
    "name",
    "lead_time_days",
    "prices",
    "reliability",
    "max_order_qty",
)
 
 
def _is_int(value) -> bool:
    """True for real integers; bool is excluded on purpose."""
    return isinstance(value, int) and not isinstance(value, bool)
 
 
def _is_number(value) -> bool:
    """True for finite ints and floats; bool, NaN and infinity are excluded."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )
 
 
@dataclass
class Supplier:
    """One supplier with its lead time, prices, reliability and capacity.
 
    distance_km and transport_mode stay in the config; the engine reads them
    from there for transport cost (SCM-F-032).
    """
 
    supplier_id: str
    name: str
    lead_time_days: int
    prices: dict
    reliability: float
    max_order_qty: int
 
    def __post_init__(self):
        for field in ("supplier_id", "name"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty string")
        if not _is_int(self.lead_time_days) or self.lead_time_days < 1:
            raise ValueError(
                f"lead_time_days must be an integer of at least 1, got {self.lead_time_days!r}"
            )
        if not isinstance(self.prices, dict) or not self.prices:
            raise ValueError("prices must be a non-empty dict of product_id to price")
        for product_id, price in self.prices.items():
            if not _is_number(price) or price < 0:
                raise ValueError(
                    f"prices for {product_id} must be a number of 0 or more, got {price!r}"
                )
        if not _is_number(self.reliability) or not 0 <= self.reliability <= 1:
            raise ValueError(
                f"reliability must be a number from 0 to 1, got {self.reliability!r}"
            )
        if not _is_int(self.max_order_qty) or self.max_order_qty < 1:
            raise ValueError(
                f"max_order_qty must be an integer of at least 1, got {self.max_order_qty!r}"
            )
 
    def supplies(self, product_id: str) -> bool:
        """True if this supplier sells the product."""
        return product_id in self.prices
 
    def price_for(self, product_id: str) -> float:
        """Unit price for the product; KeyError if this supplier does not sell it."""
        if not self.supplies(product_id):
            raise KeyError(f"supplier {self.supplier_id} does not supply {product_id}")
        return self.prices[product_id]
 
    @classmethod
    def from_dict(cls, data: dict) -> "Supplier":
        """Build a Supplier from one entry of the suppliers list in the config.
 
        Extra keys such as distance_km and transport_mode are ignored.
        """
        for key in REQUIRED_KEYS:
            if key not in data:
                raise ValueError(f"supplier is missing required key '{key}'")
        values = {key: data[key] for key in REQUIRED_KEYS}
        if isinstance(values["prices"], dict):
            values["prices"] = dict(values["prices"])
        return cls(**values)
 