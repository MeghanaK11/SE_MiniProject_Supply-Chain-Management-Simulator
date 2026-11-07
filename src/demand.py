import math


class DemandGenerator:
    """Generate daily customer demand using configured patterns."""

    def __init__(
        self,
        pattern,
        base,
        rng,
        spread=0,
        amplitude=0,
        period=1
    ):
        if pattern not in ("constant", "uniform", "seasonal"):
            raise ValueError("Unsupported demand pattern")

        if not isinstance(base, int) or isinstance(base, bool) or base < 0:
            raise ValueError("Base demand must be a non-negative integer")

        if not isinstance(spread, int) or isinstance(spread, bool) or spread < 0:
            raise ValueError("Spread must be a non-negative integer")

        if not isinstance(amplitude, int) or isinstance(amplitude, bool) or amplitude < 0:
            raise ValueError("Amplitude must be a non-negative integer")

        if not isinstance(period, int) or isinstance(period, bool) or period <= 0:
            raise ValueError("Period must be a positive integer")

        if pattern == "uniform" and spread > base:
            raise ValueError("Spread cannot exceed base demand")

        self.pattern = pattern
        self.base = base
        self.rng = rng
        self.spread = spread
        self.amplitude = amplitude
        self.period = period

    def demand_for_day(self, day):
        """Return demand for a zero-based simulation day."""

        if not isinstance(day, int) or isinstance(day, bool) or day < 0:
            raise ValueError("Day must be a non-negative integer")

        if self.pattern == "constant":
            return self.base

        if self.pattern == "uniform":
            return self.rng.randint(
                self.base - self.spread,
                self.base + self.spread
            )

        if self.pattern == "seasonal":
            seasonal_change = self.amplitude * math.sin(
                2 * math.pi * day / self.period
            )
            return max(0, round(self.base + seasonal_change))

        raise ValueError("Unsupported demand pattern")

    @classmethod
    def from_config(cls, config, rng):
        """Create a DemandGenerator from one product's demand configuration."""

        if not isinstance(config, dict):
            raise ValueError("Demand configuration must be a dictionary")

        pattern = config.get("pattern")
        base = config.get("base")

        if pattern == "uniform":
            return cls(
                pattern=pattern,
                base=base,
                spread=config.get("spread", 0),
                rng=rng
            )

        if pattern == "seasonal":
            return cls(
                pattern=pattern,
                base=base,
                amplitude=config.get("amplitude", 0),
                period=config.get("period", 1),
                rng=rng
            )

        if pattern == "constant":
            return cls(
                pattern=pattern,
                base=base,
                rng=rng
            )

        raise ValueError("Unsupported demand pattern in configuration")