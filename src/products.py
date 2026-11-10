"""Product data and the product catalog for the supply chain simulator
(SCM-F-001, SCM-F-002)."""
import math
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
            if not math.isfinite(value):
                raise ValueError(f"{field} must be a finite number, got {value!r}")
            if value < 0:
                raise ValueError(f"{field} must be 0 or more, got {value!r}")

    @classmethod
    def from_dict(cls, data: dict) -> "Product":
        """Build a Product from one entry of the products list in the config."""
        for key in REQUIRED_KEYS:
            if key not in data:
                raise ValueError(f"product is missing required key '{key}'")
        return cls(**{key: data[key] for key in REQUIRED_KEYS})


class ProductCatalog:
    """All products in a scenario, looked up by product ID (SCM-F-002)."""

    def __init__(self):
        self._products = {}

    def add(self, product: Product) -> None:
        """Add a product; a product ID that is already present is rejected."""
        if not isinstance(product, Product):
            raise ValueError(f"expected a Product, got {type(product).__name__}")
        if product.product_id in self._products:
            raise ValueError(f"duplicate product_id '{product.product_id}'")
        self._products[product.product_id] = product

    def get(self, product_id: str) -> Product:
        """Return the product with this ID; KeyError if it does not exist."""
        if product_id not in self._products:
            raise KeyError(f"unknown product_id '{product_id}'")
        return self._products[product_id]

    def remove(self, product_id: str) -> None:
        """Remove the product with this ID; KeyError if it does not exist."""
        if product_id not in self._products:
            raise KeyError(f"unknown product_id '{product_id}'")
        del self._products[product_id]

    def list_all(self) -> list:
        """All products sorted by product_id."""
        return [self._products[key] for key in sorted(self._products)]

    def __len__(self) -> int:
        return len(self._products)

    @classmethod
    def from_config(cls, product_dicts) -> "ProductCatalog":
        """Build a catalog from the products list of a scenario configuration."""
        if not isinstance(product_dicts, list):
            raise ValueError("products must be a list of product entries")
        catalog = cls()
        for data in product_dicts:
            if not isinstance(data, dict):
                raise ValueError("each product entry must be an object")
            catalog.add(Product.from_dict(data))
        return catalog
