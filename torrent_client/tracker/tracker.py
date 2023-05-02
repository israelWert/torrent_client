import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple

from torrent_client.torrent_file.file import File
from torrent_client.tracker.clock import AbstractClock, Clock
from torrent_client.tracker.tracker_bridge import TrackerBridge
from torrent_client.tracker.exceptions import TrackerCommotionError, TrackerCommunicationStoppedWarning, \
    TrackerFailedTooManyTimesError, TrackerNotRespondingError
from torrent_client.tracker.tracker_logic import AbstractTrackerLogic, TrackerLogic
from torrent_client.tracker.tracker_protocol import TrackerProtocol
from torrent_client.tracker.tracker_request import TrackerRequest
from torrent_client.tracker.tracker_response import TrackerResponse

logger = logging.getLogger(__name__)


class AbstractTracker(ABC):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    async def has_stopped(self) -> bool:
        pass

    @abstractmethod
    def update(self) -> Optional[List[dict]]:
        pass


class Tracker(AbstractTracker):
    def __init__(
            self,
            download_bridge: TrackerBridge,
            protocol: TrackerProtocol,
            peer_id: bytes = None,
            file: File = None,
            logic: AbstractTrackerLogic = None,
            clock: AbstractClock = None
    ):
        self._clock = clock if clock else Clock()
        self._logic = logic if logic else TrackerLogic(file, peer_id)
        self._protocol = protocol
        self._downloading = True
        self._download_bridge = download_bridge
        self._communication_task = None
        self._response: Optional[TrackerResponse] = None

    def stop(self):
        self._downloading = False

    def start(self):
        self._communication_task = asyncio.create_task(self._communication())

    def has_stopped(self):
        return self._communication_task.done()

    def update(self) -> Optional[List[dict]]:
        if self._response:
            logger.info("got _responses")
            logger.debug(f"_responses {self._response}")
            response, peers = self._response, self._response.peers
            return peers

        if not self._communication_task.done():
            return
        self._check_communication_errors()

    def _check_communication_errors(self):
        try:
            exe = self._communication_task.exception()
            if exe is None:
                logger.warning("the tracker communication was stopped from unknown reason")
                raise TrackerCommunicationStoppedWarning
            raise exe
        except TrackerFailedTooManyTimesError:
            logger.info(f"can not connect to tracker {self._protocol.get_tracker_url()}")
            pass
        except TrackerNotRespondingError:
            logger.info(f"can not connect find {self._protocol.get_tracker_url()}")
            pass

    def _update_logic(self, response, error) -> Optional[TrackerRequest]:
        return self._logic.update(
            *self._download_bridge.get_downloaded_uploaded(),
            connection_error=error,
            response=response,
            downloading=self._downloading
        )

    async def _send_message(self, message) -> None:
        await self._protocol.send_message(
            message,
            with_response=not self._logic.end_communication_with_tracker()
        )

    async def _get_response(self) -> Tuple[Optional[TrackerResponse], bool]:
        try:
            response = await self._protocol.get_response()
            self._response = response
            if not response:
                return None, False
            return response, False
        except TrackerCommotionError:
            return None, True

    async def _communication_loop(self):
        communication_data = dict()
        while not self._logic.end_communication_with_tracker():
            message = self._update_logic(
                communication_data.pop("responses", None),
                communication_data.pop("error", False))
            if message:
                await self._send_message(message)
            communication_data["responses"], communication_data["error"] = await self._get_response()
            if not self._logic.end_communication_with_tracker():
                await self._clock.sleep(5)

    async def _communication(self):
        logger.info("starting a new communication with tracker")
        async with self._protocol:
            await self._communication_loop()
            logger.info(" tracker communication is closed")


"""0       64-bit integer  _connection_id
Offset  Size    Name    Value
0       64-bit integer  _connection_id
8       32-bit integer  action          1 // announce
12      32-bit integer  transaction_id
16      20-byte string  info_hash
36      20-byte string  peer_id
56      64-bit integer  downloaded
64      64-bit integer  left
72      64-bit integer  uploaded
80      32-bit integer  event           0 // 0: none; 1: completed; 2: started; 3: stopped
84      32-bit integer  IP address      0 // default
88      32-bit integer  key
92      32-bit integer  num_want        -1 // default
96      16-bit integer  port
98"""