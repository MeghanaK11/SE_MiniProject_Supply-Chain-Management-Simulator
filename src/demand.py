"""Demand generation for supply-chain simulations."""

import math
import random
from typing import Any


class DemandGenerator:
    """Generate daily demand using constant, uniform or seasonal patterns."""

    def __init__(
        self,
        pattern: str,
        base: int,
        rng: random.Random | None = None,
        spread: int = 0,
        amplitude: float = 0,
        period: int = 7,
    ) -> None:
        """Initialize and validate a demand generator."""
        if pattern not in {"constant", "uniform", "seasonal"}:
            raise ValueError(
                "pattern must be 'constant', 'uniform' or 'seasonal'"
            )

        if type(base) is not int or base < 0:
            raise ValueError("base must be a non-negative integer")

        if type(spread) is not int or spread < 0:
            raise ValueError("spread must be a non-negative integer")

        if isinstance(amplitude, bool) or not isinstance(
            amplitude, (int, float)
        ):
            raise ValueError("amplitude must be a finite non-negative number")

        if not math.isfinite(amplitude) or amplitude < 0:
            raise ValueError("amplitude must be a finite non-negative number")

        if type(period) is not int or period <= 0:
            raise ValueError("period must be a positive integer")

        if pattern == "uniform" and rng is None:
            raise ValueError("rng is required for uniform demand")

        if rng is not None and not callable(getattr(rng, "randint", None)):
            raise TypeError("rng must provide a randint method")

        self.pattern = pattern
        self.base = base
        self.rng = rng
        self.spread = spread
        self.amplitude = float(amplitude)
        self.period = period

    @classmethod
    def from_config(
        cls,
        config: dict[str, Any],
        rng: random.Random | None = None,
    ) -> "DemandGenerator":
        """Create a demand generator from a configuration dictionary."""
        if not isinstance(config, dict):
            raise TypeError("config must be a dictionary")

        return cls(
            pattern=config.get("pattern", "constant"),
            base=config.get("base", 0),
            rng=rng,
            spread=config.get("spread", 0),
            amplitude=config.get("amplitude", 0),
            period=config.get("period", 7),
        )

    def demand_for_day(self, day: int) -> int:
        """Return the generated demand for the requested simulation day."""
        if type(day) is not int or day < 0:
            raise ValueError("day must be a non-negative integer")

        if self.pattern == "constant":
            return self.base

        if self.pattern == "uniform":
            lower = max(0, self.base - self.spread)
            upper = self.base + self.spread
            return self.rng.randint(lower, upper)

        seasonal_value = self.base + self.amplitude * math.sin(
            2 * math.pi * day / self.period
        )

        return max(0, round(seasonal_value))