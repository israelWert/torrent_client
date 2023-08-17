from enum import Enum, auto


class Event(Enum):
    NoEvent = auto()
    Start = auto()
    Complete = auto()

    @staticmethod
    def to_http(event: "Event"):
        if event == Event.Start:
            return "started"
        elif event == Event.Complete:
            return "completed"

    @staticmethod
    def to_udp(event: "Event"):
        if event == Event.Complete:
            return 1
        if event in (Event.NoEvent, Event.Start):
            return 0
