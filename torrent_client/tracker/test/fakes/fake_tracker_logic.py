from typing import Optional

from torrent_client.tracker.tracker_logic import AbstractTrackerLogic
from torrent_client.tracker.tracker_request import TrackerRequest
from torrent_client.tracker.tracker_response import TrackerResponse


class FakeTrackerLogic(AbstractTrackerLogic):
    def __init__(self):
        self.request = None
        self.response = None
        self.is_time_for_next = False
        self.is_time_for_next = True
        self.is_completed = False
        self.connection_errors = 0

    def update(self, uploaded: int, downloaded: int, connection_error: bool = False,
               response: Optional[TrackerResponse] = None, downloading: bool = False) -> Optional[TrackerRequest]:
        if connection_error:
            self.connection_errors += 1
        self.is_completed = not downloading
        if response:
            self.response = response
        if self.is_time_for_next:
            self.is_time_for_next = False
            return self.request

    def end_communication_with_tracker(self):
        return self.is_completed

