
EVENT_TYPES = (
    "DEMAND",
    "SHIPMENT",
    "STOCKOUT",
    "PO_PLACED",
    "PO_DELAYED",
    "PO_RECEIVED",
)


class SimulationClock:
    def __init__(self, total_days: int):
        if isinstance(total_days, bool) or not isinstance(total_days, int) or total_days < 1:
            raise ValueError(
                f"total_days must be an integer of at least 1, got {total_days!r}"
            )

        self.total_days = total_days
        self._current_day = 0

    @property
    def current_day(self) -> int:
        return self._current_day

    def advance(self) -> int:
        if self.is_finished():
            raise RuntimeError("Simulation has finished")

        self._current_day += 1
        return self._current_day

    def is_finished(self) -> bool:
        return self._current_day == self.total_days


class EventLog:
    def __init__(self):
        self._events = []

    def record(self, day: int, event_type: str, message: str) -> None:
        if isinstance(day, bool) or not isinstance(day, int) or day < 0:
            raise ValueError(f"day must be a non-negative integer, got {day!r}")

        if event_type not in EVENT_TYPES:
            raise ValueError(f"Invalid event type: {event_type!r}")

        if not isinstance(message, str) or not message.strip():
            raise ValueError(f"message must be a non-empty string, got {message!r}")

        self._events.append({
            "day": day,
            "type": event_type,
            "message": message,
        })

    def events(self, event_type: str | None = None) -> list[dict]:
        if event_type is not None and event_type not in EVENT_TYPES:
            raise ValueError(f"Invalid event type: {event_type!r}")

        result = self._events

        if event_type is not None:
            result = [
                event for event in self._events
                if event["type"] == event_type
            ]

        return [event.copy() for event in result]

    def count(self, event_type: str) -> int:
        if event_type not in EVENT_TYPES:
            raise ValueError(f"Invalid event type: {event_type!r}")

        return sum(
            1 for event in self._events
            if event["type"] == event_type
        )
