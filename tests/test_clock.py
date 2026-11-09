import pytest
from src.clock import SimulationClock, EventLog


def test_clock_starts_at_zero():
    clock = SimulationClock(3)
    assert clock.current_day == 0
    assert clock.is_finished() is False


def test_clock_advance():
    clock = SimulationClock(3)
    assert clock.advance() == 1
    assert clock.current_day == 1


def test_clock_finishes():
    clock = SimulationClock(3)
    clock.advance()
    clock.advance()
    clock.advance()
    assert clock.is_finished() is True

    with pytest.raises(RuntimeError):
        clock.advance()


def test_event_filter_and_count():
    log = EventLog()
    log.record(0, "DEMAND", "Demand generated")
    log.record(0, "DEMAND", "New demand")
    log.record(1, "SHIPMENT", "Products shipped")

    assert log.count("DEMAND") == 2
    assert log.count("SHIPMENT") == 1
    assert len(log.events("DEMAND")) == 2
    assert len(log.events()) == 3


def test_invalid_inputs():
    with pytest.raises(ValueError):
        SimulationClock(0)

    log = EventLog()
    with pytest.raises(ValueError):
        log.record(0, "FOO", "Invalid event")