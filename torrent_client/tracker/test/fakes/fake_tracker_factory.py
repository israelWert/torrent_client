from typing import List

from torrent_client.tracker.tracker import AbstractTracker
from torrent_client.tracker.tracker_factory import AbstractTrackerFactory


class FakeTrackerFactory(AbstractTrackerFactory):
    def __init__(self):
        self.list = []

    def create_trackers(self) -> List[AbstractTracker]:
        return self.list
