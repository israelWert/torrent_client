from abc import ABC, abstractmethod
from typing import Optional

from torrent_client.tracker.tracker_request import TrackerRequest
from torrent_client.tracker.tracker_response import TrackerResponse


class TrackerProtocol(ABC):
    @abstractmethod
    async def __aenter__(self):
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    async def send_message(self, req: TrackerRequest, with_response: bool = True) -> None:
        pass

    @abstractmethod
    async def get_response(self) -> Optional[TrackerResponse]:
        pass

    @abstractmethod
    def get_tracker_url(self):
        pass
