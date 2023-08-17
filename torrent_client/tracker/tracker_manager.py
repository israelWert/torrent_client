import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict

from torrent_client.torrent_file.torrent_file import TorrentFile
from torrent_client.tracker.clock import AbstractClock, Clock
from torrent_client.tracker.exceptions import TrackerStoppedNoUnknownReasonError, TrackerFailedTooManyTimesError, \
    TrackerNotRespondingError, NoTrackerLeftError
from torrent_client.tracker.tracker_bridge import TrackerBridge
from torrent_client.tracker.tracker_factory import AbstractTrackerFactory, TrackerFactory


logger = logging.getLogger(__name__)


class AbstractTrackerManager(ABC):

    @abstractmethod
    async def start_trackers(self,
                       peer_que: asyncio.Queue,
                       peer_id: str = None,
                       bridge: TrackerBridge = None,
                       file: TorrentFile = None, ) -> None:
        pass


class TrackerManager(AbstractTrackerManager):
    def __init__(self,
                 factory: AbstractTrackerFactory = None,
                 clock: AbstractClock = None,
                 ):
        self._factory = factory if factory else None
        self._clock = clock if clock else Clock()
        self._trackers = []

    async def start_trackers(self,
                       peer_que: asyncio.Queue,
                       peer_id: str = None,
                       bridge: TrackerBridge = None,
                       file: TorrentFile = None,
                       ) -> None:
        self._factory = self._factory if self._factory else TrackerFactory(
            bridge=bridge,
            file=file,
            peer_id=peer_id,
            peer_que=peer_que
        )
        logger.info("**************** creating trackers ****************")
        self._trackers = self._factory.create_trackers()
        logger.info("**************** all tracker were created ****************")
        logger.info("**************** start trackers ****************")
        await asyncio.gather(*[tracker.communicate() for tracker in self._trackers])
        logger.info("**************** all tracker were started ****************")

