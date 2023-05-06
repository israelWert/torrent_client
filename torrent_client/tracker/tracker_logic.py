import logging
from abc import ABC, abstractmethod
from typing import Optional

from torrent_client.torrent_file.file import File
from torrent_client.tracker.clock import Clock, AbstractClock
from torrent_client.tracker.event import Event
from torrent_client.tracker.exceptions import TrackerFailedTooManyTimesError
from torrent_client.tracker.net.tracker_protocol import TrackerRequest, TrackerResponse

DEFAULT_PORT = 6881
MAX_FAILURES = 3
INTERVAL_IN_FAILURE = 5
logger = logging.getLogger(__name__)


class AbstractTrackerLogic(ABC):
    @abstractmethod
    def update(self,
               uploaded: int,
               downloaded: int,
               connection_error: bool = False,
               response: Optional[TrackerResponse] = None,
               downloading: bool = False) -> Optional[TrackerRequest]:
        pass

    @abstractmethod
    def end_communication_with_tracker(self):
        pass


class TrackerLogic(AbstractTrackerLogic):
    def __init__(self, file: File, peer_id: str, clock: AbstractClock = None):
        self._file = file
        self._has_started = False
        self._completed = False
        self._failures = 0
        self._peer_id = peer_id
        self._clock = clock if clock else Clock()
        self._end_time = 0

    def end_communication_with_tracker(self):
        return self._completed

    def update(self,
               uploaded: int,
               downloaded: int,
               connection_error: bool = False,
               response: Optional[TrackerResponse] = None,
               downloading: bool = True) -> Optional[TrackerRequest]:
        if self._interval_tracking(connection_error, response) or not downloading:
            self._completed = not downloading
            return self._create_message(uploaded, downloaded)

    def _interval_tracking(self, connection_error: bool, response: Optional[TrackerResponse]) -> bool:
        if response:
            self._has_started = True
            self._set_interval(response.interval)
        if connection_error:
            self._set_error_interval()
        if self._is_time_for_next_message():
            self._end_time = -1
            return True
        return False

    def _create_message(self, uploaded: int, downloaded: int):
        logger.info("creating new request")
        return TrackerRequest(
            info_hash=self._file.info_hash,
            peer_id=self._peer_id,
            port=DEFAULT_PORT,
            uploaded=uploaded,
            downloaded=downloaded,
            left=self._file.total_size - (uploaded + downloaded),
            event=self._current_event(),
        )

    def _current_event(self):
        if not self._has_started:
            return Event.Start
        if self._completed:
            return Event.Complete

    def _set_error_interval(self):
        self._set_interval((2 ** self._failures) * INTERVAL_IN_FAILURE)
        self._failures += 1
        if self._failures > MAX_FAILURES:
            raise TrackerFailedTooManyTimesError(self._failures)

    def _is_time_for_next_message(self):
        return self._end_time - self._clock.get_time() <= 0 and self._end_time != -1

    def _set_interval(self, interval):
        self._end_time = self._clock.get_time() + interval

