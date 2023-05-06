import logging
from abc import ABC, abstractmethod
from typing import List, Dict

from torrent_client.torrent_file.file import File
from torrent_client.tracker.clock import AbstractClock, Clock
from torrent_client.tracker.exceptions import TrackerStoppedNoUnknownReasonError, TrackerFailedTooManyTimesError, \
    TrackerNotRespondingError, NoTrackerLeftError
from torrent_client.tracker.tracker_bridge import TrackerBridge
from torrent_client.tracker.tracker_factory import AbstractTrackerFactory, TrackerFactory


logger = logging.getLogger(__name__)


class AbstractTrackerManager(ABC):

    @abstractmethod
    def start_trackers(self,
                       peer_id: str = None,
                       bridge: TrackerBridge = None,
                       file: File = None,) -> None:
        pass

    @abstractmethod
    def get_peers(self) -> List[Dict[str, str]]:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass


class TrackerManager(AbstractTrackerManager):
    def __init__(self,
                 factory: AbstractTrackerFactory = None,
                 clock: AbstractClock = None,
                 ):
        self._factory = factory if factory else None
        self._clock = clock if clock else Clock()
        self._trackers = []

    def start_trackers(self,
                       peer_id: str = None,
                       bridge: TrackerBridge = None,
                       file: File = None,
                       ) -> None:
        self._factory = self._factory if self._factory else TrackerFactory(
            bridge=bridge,
            file=file,
            peer_id=peer_id
        )
        logger.info("**************** creating trackers ****************")
        self._trackers = self._factory.create_trackers()
        logger.info("**************** all tracker were created ****************")
        logger.info("**************** start trackers ****************")
        for tracker in self._trackers:
            tracker.start()
        logger.info("**************** all tracker were started ****************")

    def get_peers(self) -> List[Dict[str, str]]:
        peers = []
        logger.info("**************** receiving trackers data ****************")
        for tracker in self._trackers[:]:
            try:
                new_peers = tracker.get_peers()
            except (TrackerStoppedNoUnknownReasonError, TrackerFailedTooManyTimesError, TrackerNotRespondingError) as e:
                logger.warning(f"tracker was stopped with error {e}")
                self._trackers.remove(tracker)
            else:
                if new_peers:
                    peers.extend(new_peers)
        logger.info("**************** end receiving ****************")
        if len(self._trackers) == 0:
            logger.critical("no tracker left")
            raise NoTrackerLeftError("no tracker run check your internet and the provided torrent file")
        return peers

    async def stop(self) -> None:
        for tracker in self._trackers:
            tracker.stop()

        while any([not tracker.has_stopped() for tracker in self._trackers]):
            await self._clock.sleep(0.1)

