import asyncio
import logging
from abc import ABC, abstractmethod
from asyncio import Queue
from typing import Optional, List, Tuple

from torrent_client.constants import PEER_DEFAULT_PORT
from torrent_client.torrent_file.torrent_file import TorrentFile
from torrent_client.tracker.clock import AbstractClock, Clock
from torrent_client.tracker.event import Event
from torrent_client.tracker.tracker_bridge import TrackerBridge
from torrent_client.tracker.net.tracker_protocol import TrackerProtocol
from torrent_client.tracker.tracker_request import TrackerRequest
from torrent_client.tracker.tracker_response import TrackerResponse

logger = logging.getLogger(__name__)


class AbstractTracker(ABC):
    @abstractmethod
    async def communicate(self):
        pass


class Tracker(AbstractTracker):
    def __init__(
            self,
            file: TorrentFile,
            peer_id: str,
            peer_queue: Queue,
            download_bridge: TrackerBridge,
            protocol: TrackerProtocol,
            clock: AbstractClock = None
    ):
        self._total_size = file.total_size
        self._peer_id = peer_id
        self._info_hash = file.info_hash
        self._clock = clock if clock else Clock()
        self._protocol = protocol
        self._download_bridge = download_bridge
        self._peer_queue = peer_queue
        self._current_event = Event.Start
        self._is_running = True

    async def communicate(self):
        logger.info("tracker was started")
        async with self._protocol:
            while self._is_running:
                last_response = await self._exchange_messages()
                if last_response:
                    await self._peer_queue.put(last_response.peers)
                    await self._sleep(last_response.interval)
                await self._process_connection_and_downloading_updates()
        logger.info("tracker communication is closed")


    async def _sleep(self, interval) -> None:
        await self._clock.sleep(
            interval,
            lambda: not(self._protocol.is_connected() and self._is_running)
        )

    async def _process_connection_and_downloading_updates(self):
        if self._current_event == Event.Start:
            self._current_event = Event.NoEvent
        self._process_downloading_updates()


    def _process_downloading_updates(self) -> None:
        if not self._download_bridge.is_downloading():
            if self._current_event.Complete:
                self._is_running = False
            else:
                self._current_event = Event.Complete

    async def _exchange_messages(self) -> Optional[TrackerResponse]:
        message = self._create_message()
        logger.info("sending new message")
        logger.debug(f"message data: {message}")
        return await self._protocol.send_message(
            message,
            with_response=not(self._current_event == Event.Complete)
        )


    def _create_message(self) -> TrackerRequest:
        logger.info("creating new request")
        uploaded_downloaded = self._download_bridge.get_downloaded_uploaded()
        return TrackerRequest(
            info_hash=self._info_hash,
            peer_id=self._peer_id,
            port=PEER_DEFAULT_PORT,
            uploaded=uploaded_downloaded[0],
            downloaded=uploaded_downloaded[1],
            left=self._total_size - sum(uploaded_downloaded),
            event=self._current_event,
        )





