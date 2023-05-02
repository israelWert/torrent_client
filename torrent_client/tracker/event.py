from enum import Enum, auto


class Event(Enum):
    Start = auto()
    Complete = auto()

    @staticmethod
    def to_http(event: "Event"):
        if event.Start:
            return "start"
        elif event.Complete:
            return "completed"

    @staticmethod
    def to_udp(event: "Event"):
        if event.Complete:
            return 1
        return 0
