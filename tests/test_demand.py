
"""Tests for demand generation (SCM-F-020)."""

import random

import pytest

from src.demand import DemandGenerator


# TC-DEM-01: Constant demand

def test_constant_demand():
    generator = DemandGenerator(
        pattern="constant",
        base=4,
    )

    assert generator.period == 7
    assert [generator.demand_for_day(day) for day in range(5)] == [
        4, 4, 4, 4, 4
    ]

    config_generator = DemandGenerator.from_config(
        {"pattern": "constant", "base": 4}
    )
    assert config_generator.period == 7


# TC-DEM-02: Uniform demand

def test_uniform_demand_range_200_days():
    generator = DemandGenerator(
        pattern="uniform",
        base=20,
        spread=5,
        rng=random.Random(42),
    )

    demands = [
        generator.demand_for_day(day)
        for day in range(200)
    ]

    assert all(15 <= demand <= 25 for demand in demands)


def test_uniform_spread_greater_than_base():
    """TC-DEM-02: Spread greater than base is valid."""
    generator = DemandGenerator(
        pattern="uniform",
        base=2,
        spread=5,
        rng=random.Random(42),
    )

    demands = [
        generator.demand_for_day(day)
        for day in range(200)
    ]

    assert all(0 <= demand <= 7 for demand in demands)


# TC-DEM-03: Reproducibility

def test_same_seed_produces_same_sequence():
    generator1 = DemandGenerator(
        pattern="uniform",
        base=20,
        spread=5,
        rng=random.Random(123),
    )

    generator2 = DemandGenerator(
        pattern="uniform",
        base=20,
        spread=5,
        rng=random.Random(123),
    )

    results1 = [
        generator1.demand_for_day(day) for day in range(200)
    ]
    results2 = [
        generator2.demand_for_day(day) for day in range(200)
    ]

    assert results1 == results2


# TC-DEM-04: Seasonal demand through from_config

def test_seasonal_demand_from_config():
    config = {
        "pattern": "seasonal",
        "base": 8,
        "amplitude": 3,
        "period": 4,
    }

    generator = DemandGenerator.from_config(config)

    demands = [
        generator.demand_for_day(day)
        for day in range(4)
    ]

    assert demands == [8, 11, 8, 5]


# TC-DEM-05: Invalid inputs

@pytest.mark.parametrize(
    "factory",
    [
        pytest.param(
            lambda: DemandGenerator("unknown", 4),
            id="unknown-pattern",
        ),
        pytest.param(
            lambda: DemandGenerator("constant", -1),
            id="negative-base",
        ),
        pytest.param(
            lambda: DemandGenerator("uniform", 4, random.Random(1), -1),
            id="negative-spread",
        ),
        pytest.param(
            lambda: DemandGenerator(
                "seasonal", 4, amplitude=-1
            ),
            id="negative-amplitude",
        ),
        pytest.param(
            lambda: DemandGenerator(
                "seasonal", 4, period=0
            ),
            id="zero-period",
        ),
        pytest.param(
            lambda: DemandGenerator("uniform", 4),
            id="uniform-without-rng",
        ),
        pytest.param(
            lambda: DemandGenerator(
                "constant", 4
            ).demand_for_day(-1),
            id="negative-day",
        ),
        pytest.param(
            lambda: DemandGenerator.from_config([]),
            id="non-dictionary-config",
        ),
    ],
)
def test_invalid_inputs(factory):
    with pytest.raises(ValueError):
        factory()
