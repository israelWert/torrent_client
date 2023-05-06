import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple

from torrent_client.torrent_file.file import File
from torrent_client.tracker.clock import AbstractClock, Clock
from torrent_client.tracker.tracker_bridge import TrackerBridge
from torrent_client.tracker.exceptions import TrackerCommotionError, TrackerCommunicationStoppedWarning, \
    TrackerFailedTooManyTimesError, TrackerNotRespondingError, TrackerStoppedNoUnknownReasonError
from torrent_client.tracker.tracker_logic import AbstractTrackerLogic, TrackerLogic
from torrent_client.tracker.net.tracker_protocol import TrackerProtocol
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
    def has_stopped(self) -> bool:
        pass

    @abstractmethod
    def get_peers(self) -> Optional[List[dict]]:
        pass


class Tracker(AbstractTracker):
    def __init__(
            self,
            download_bridge: TrackerBridge,
            protocol: TrackerProtocol,
            peer_id: str = None,
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
        logger.info("tracker start stopping")
        self._downloading = False

    def start(self):
        logger.info("tracker was started")
        self._communication_task = asyncio.create_task(self._communication())

    def has_stopped(self):
        return self._communication_task.done()

    def get_peers(self) -> Optional[List[dict]]:
        if self._response:
            logger.info("returning response")
            logger.debug(f"responses: {self._response}")
            peers = self._response.peers
            return peers
        if not self._communication_task.done():
            return
        self._check_communication_errors()

    async def _communication(self):
        logger.info("starting a new communication with tracker")
        async with self._protocol:
            await self._communication_loop()
        logger.info("tracker communication is closed")

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

    async def _get_response(self) -> Tuple[Optional[TrackerResponse], bool]:
        try:
            response = await self._protocol.get_response()
            self._response = response
            if not response:
                return None, False
            logger.info("response was received")
            return response, False
        except TrackerCommotionError:
            logger.warning("tracker protocol raised error")
            return None, True

    def _check_communication_errors(self):
        try:
            exe = self._communication_task.exception()
            if exe is None:
                logger.warning("the tracker communication was stopped from unknown reason")
                raise TrackerStoppedNoUnknownReasonError
            raise TrackerStoppedNoUnknownReasonError from exe
        except (TrackerFailedTooManyTimesError, TrackerNotRespondingError) as e:
            logger.warning(f"can not connect to tracker {self._protocol.get_tracker_url()}")
            raise e

    def _update_logic(self, response, error) -> Optional[TrackerRequest]:
        return self._logic.update(
            *self._download_bridge.get_downloaded_uploaded(),
            connection_error=error,
            response=response,
            downloading=self._downloading
        )

    async def _send_message(self, message: TrackerRequest) -> None:
        logger.info("sending new message")
        logger.debug(f"message data: {message}")
        await self._protocol.send_message(
            message,
            with_response=not self._logic.end_communication_with_tracker()
        )




