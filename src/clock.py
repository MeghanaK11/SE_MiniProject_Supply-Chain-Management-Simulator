EVENT_TYPES = (
    "DEMAND", "SHIPMENT", "STOCKOUT",
    "PO_PLACED", "PO_DELAYED", "PO_RECEIVED"
)


class SimulationClock:
    def __init__(self, total_days: int):
        if total_days < 1:
            raise ValueError("total_days must be at least 1")
        self.total_days = total_days
        self._current_day = 0

    @property
    def current_day(self):
        return self._current_day

    def advance(self):
        if self.is_finished():
            raise RuntimeError("Simulation has finished")
        self._current_day += 1
        return self._current_day

    def is_finished(self):
        return self._current_day == self.total_days


class EventLog:
    def __init__(self):
        self._events = []

    def record(self, day, event_type, message):
        if event_type not in EVENT_TYPES:
            raise ValueError("Invalid event type")
        self._events.append({
            "day": day,
            "type": event_type,
            "message": message
        })

    def events(self, event_type=None):
        if event_type is not None and event_type not in EVENT_TYPES:
            raise ValueError("Invalid event type")

        if event_type is None:
            return [event.copy() for event in self._events]

        return [
            event.copy() for event in self._events
            if event["type"] == event_type
        ]

    def count(self, event_type):
        if event_type not in EVENT_TYPES:
            raise ValueError("Invalid event type")
        return sum(1 for event in self._events
                   if event["type"] == event_type)