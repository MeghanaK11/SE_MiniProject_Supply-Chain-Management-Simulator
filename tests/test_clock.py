
"""Tests for simulation clock and event log."""

import pytest

from src.clock import SimulationClock, EventLog


def test_clock_starts_at_zero():
    """TC-CLK-01: Clock starts at day zero and is not finished."""
    clock = SimulationClock(3)

    assert clock.current_day == 0
    assert clock.is_finished() is False


def test_clock_advance():
    """TC-CLK-02: Clock advances and returns day one."""
    clock = SimulationClock(3)

    result = clock.advance()

    assert result == 1
    assert clock.current_day == 1


def test_clock_finishes():
    """TC-CLK-03: Clock finishes after three advances."""
    clock = SimulationClock(3)

    clock.advance()
    clock.advance()
    clock.advance()

    assert clock.current_day == 3
    assert clock.is_finished() is True

    with pytest.raises(RuntimeError):
        clock.advance()


def test_event_filter_and_count():
    """TC-CLK-04: Event filtering and counting work correctly."""
    log = EventLog()

    log.record(0, "DEMAND", "Demand generated")
    log.record(1, "DEMAND", "Demand generated again")
    log.record(1, "SHIPMENT", "Shipment received")

    assert log.count("DEMAND") == 2
    assert log.count("SHIPMENT") == 1

    assert len(log.events("DEMAND")) == 2
    assert len(log.events("SHIPMENT")) == 1
    assert len(log.events()) == 3


def test_invalid_inputs():
    """TC-CLK-05: Invalid clock and event log inputs raise ValueError."""
    invalid_days = [0, -1, 2.5, "3", None, True]

    for days in invalid_days:
        with pytest.raises(ValueError):
            SimulationClock(days)

    log = EventLog()

    with pytest.raises(ValueError):
        log.record(-1, "DEMAND", "Invalid day")

    with pytest.raises(ValueError):
        log.record(True, "DEMAND", "Invalid day")

    with pytest.raises(ValueError):
        log.record(0, "DEMAND", "")

    with pytest.raises(ValueError):
        log.record(0, "DEMAND", "   ")

    with pytest.raises(ValueError):
        log.record(0, "FOO", "Invalid event")

    with pytest.raises(ValueError):
        log.events("FOO")

    with pytest.raises(ValueError):
        log.count("FOO")
