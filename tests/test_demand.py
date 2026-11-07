import random
import pytest

from src.demand import DemandGenerator


def test_constant_demand():
    """TC-DEM-01: Constant demand returns the base every day."""
    generator = DemandGenerator(
        pattern="constant",
        base=4,
        rng=random.Random(42)
    )

    assert [generator.demand_for_day(day) for day in range(5)] == [
        4, 4, 4, 4, 4
    ]


def test_uniform_random_demand():
    """TC-DEM-02: Uniform demand stays within base plus or minus spread."""
    generator = DemandGenerator(
        pattern="uniform",
        base=20,
        spread=5,
        rng=random.Random(42)
    )

    demands = [
        generator.demand_for_day(day)
        for day in range(100)
    ]

    assert all(15 <= demand <= 25 for demand in demands)


def test_seasonal_demand():
    """TC-DEM-03: Seasonal demand follows the expected repeating pattern."""
    generator = DemandGenerator(
        pattern="seasonal",
        base=8,
        amplitude=3,
        period=4,
        rng=random.Random(42)
    )

    demands = [
        generator.demand_for_day(day)
        for day in range(4)
    ]

    assert demands == [8, 11, 8, 5]


def test_random_demand_is_repeatable():
    """TC-DEM-04: The same seed produces the same random demand sequence."""
    generator1 = DemandGenerator(
        pattern="uniform",
        base=20,
        spread=5,
        rng=random.Random(123)
    )

    generator2 = DemandGenerator(
        pattern="uniform",
        base=20,
        spread=5,
        rng=random.Random(123)
    )

    results1 = [generator1.demand_for_day(day) for day in range(10)]
    results2 = [generator2.demand_for_day(day) for day in range(10)]

    assert results1 == results2


def test_from_config():
    """TC-DEM-05: from_config creates generators from configuration."""
    config = {
        "pattern": "seasonal",
        "base": 8,
        "amplitude": 3,
        "period": 4
    }

    generator = DemandGenerator.from_config(
        config,
        random.Random(42)
    )

    assert generator.pattern == "seasonal"
    assert [
        generator.demand_for_day(day)
        for day in range(4)
    ] == [8, 11, 8, 5]


def test_invalid_pattern():
    """Unsupported demand patterns are rejected."""
    with pytest.raises(ValueError):
        DemandGenerator(
            pattern="unknown",
            base=4,
            rng=random.Random(42)
        )


def test_invalid_day():
    """Negative simulation days are rejected."""
    generator = DemandGenerator(
        pattern="constant",
        base=4,
        rng=random.Random(42)
    )

    with pytest.raises(ValueError):
        generator.demand_for_day(-1)