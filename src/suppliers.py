"""Suppliers for the supply chain simulator (SCM-F-010).
 
Also holds the supplier registry (SCM-F-011) and supplier selection
strategies (SCM-F-012).
"""
import math
from dataclasses import dataclass
 
STRATEGIES = ("cheapest", "fastest", "balanced")
 
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
 
 
class SupplierRegistry:
    """All suppliers in a scenario, looked up by ID or by product (SCM-F-011)."""
 
    def __init__(self):
        self._suppliers = {}
 
    def add(self, supplier: Supplier) -> None:
        """Add a supplier; ValueError if it is not a Supplier or its ID is already registered."""
        if not isinstance(supplier, Supplier):
            raise ValueError(f"expected a Supplier, got {supplier!r}")
        if supplier.supplier_id in self._suppliers:
            raise ValueError(f"duplicate supplier_id '{supplier.supplier_id}'")
        self._suppliers[supplier.supplier_id] = supplier
 
    def get(self, supplier_id: str) -> Supplier:
        """Return the supplier with this ID; KeyError if it is unknown."""
        if supplier_id not in self._suppliers:
            raise KeyError(f"unknown supplier_id '{supplier_id}'")
        return self._suppliers[supplier_id]
 
    def list_all(self) -> list:
        """All suppliers, sorted by supplier_id."""
        return [self._suppliers[sid] for sid in sorted(self._suppliers)]
 
    def suppliers_for(self, product_id: str) -> list:
        """Suppliers that sell the product, sorted by supplier_id."""
        return [s for s in self.list_all() if s.supplies(product_id)]
 
    @classmethod
    def from_config(cls, supplier_dicts: list) -> "SupplierRegistry":
        """Build a registry from the suppliers list of the config (cfg["suppliers"])."""
        if not isinstance(supplier_dicts, list):
            raise ValueError("suppliers must be a list of supplier entries")
        registry = cls()
        for entry in supplier_dicts:
            if not isinstance(entry, dict):
                raise ValueError(f"each supplier entry must be a dict, got {entry!r}")
            registry.add(Supplier.from_dict(entry))
        return registry
 
 
 
def _balanced_score(supplier: Supplier, sellers: list, product_id: str,
                    weights: tuple) -> float:
    """w1 x (price / highest price) + w2 x (lead time / longest lead time) + w3 x (1 - reliability)."""
    w1, w2, w3 = weights
    highest_price = max(s.price_for(product_id) for s in sellers)
    longest_lead = max(s.lead_time_days for s in sellers)
    price_part = supplier.price_for(product_id) / highest_price if highest_price else 0.0
    lead_part = supplier.lead_time_days / longest_lead
    return w1 * price_part + w2 * lead_part + w3 * (1 - supplier.reliability)
 
 
def select_supplier(candidates: list, product_id: str,
                    strategy: str = "balanced",
                    weights: tuple = (0.5, 0.3, 0.2)) -> Supplier:
    """Pick one supplier for the product (SCM-F-012).
 
    cheapest: lowest price. fastest: lowest lead time. balanced: lowest
    balanced score. Only suppliers that sell the product are compared, and
    ties go to the smaller supplier_id.
    """
    if strategy not in STRATEGIES:
        raise ValueError(f"unknown strategy '{strategy}', expected one of {STRATEGIES}")
    sellers = [s for s in candidates if s.supplies(product_id)]
    if not sellers:
        raise ValueError(f"no supplier sells {product_id}")
    if strategy == "cheapest":
        def score(s):
            return s.price_for(product_id)
    elif strategy == "fastest":
        def score(s):
            return s.lead_time_days
    else:
        def score(s):
            return _balanced_score(s, sellers, product_id, weights)
    return min(sellers, key=lambda s: (score(s), s.supplier_id))
 