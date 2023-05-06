from typing import Optional

from torrent_client.tracker.net.tracker_protocol import TrackerProtocol
from torrent_client.tracker.tracker_request import TrackerRequest
from torrent_client.tracker.tracker_response import TrackerResponse


class FakeTrackerProtocol(TrackerProtocol):
    def __init__(self):
        self.response_or_error = None
        self.request = None
        self.has_entered = False
        self.has_exit = False
        self.req = None
        self.with_response = True

    async def __aenter__(self):
        self.has_entered = True

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.has_exit = True

    async def send_message(self, req: TrackerRequest, with_response: bool = True) -> None:

        self.req = req
        self.with_response = with_response

    async def get_tracker_url(self):
        return None

    async def get_response(self) -> Optional[TrackerResponse]:
        if self.req:
            self.request = self.req
        else:
            return
        if isinstance(self.response_or_error, Exception):
            raise self.response_or_error
        return self.response_or_error

