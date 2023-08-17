import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from torrent_client.torrent_file.torrent_file import TorrentFile
from torrent_client.tracker.exceptions import TrackerNotSportedError
from torrent_client.tracker.net.http_tracker import HttpTracker
from torrent_client.tracker.net.tracker_protocol import TrackerProtocol
from torrent_client.tracker.net.udp_net.udp_tracker import UDPTracker
from torrent_client.tracker.net.udp_net.async_udp_client import AsyncUdpClient, AbstractAsyncUdpClient
from torrent_client.tracker.tracker import AbstractTracker, Tracker
from torrent_client.tracker.tracker_bridge import TrackerBridge

logger = logging.getLogger(__name__)


class AbstractTrackerFactory(ABC):
    @abstractmethod
    def create_trackers(self) -> List[AbstractTracker]:
        pass

    @abstractmethod
    async def __aenter__(self):
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class TrackerFactory(AbstractTrackerFactory):
    def __init__(self, bridge: TrackerBridge, file: TorrentFile, peer_id: str, peer_que: asyncio.Queue, udp_client: AbstractAsyncUdpClient = None):
        self.file = file
        self._bridge = bridge
        self._udp_client = udp_client
        self._peer_id = peer_id
        self._peer_que = peer_que

    async def __aenter__(self):
        if not self._udp_client:
            self._udp_client = AsyncUdpClient()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._udp_client.close()

    def _find_protocol(self, url) -> Optional[TrackerProtocol]:
        protocol = None
        if "http" in url:
            protocol = HttpTracker(url)
        elif "udp" in url:
            try:
                protocol = UDPTracker(url, self._udp_client)
            except TrackerNotSportedError:
                logger.warning(f"tracker {url} using ip6")
                return None
        else:
            logger.warning(f"tracker {url} with unknown protocol")
        return protocol

    def _create_tracker(self, protocol: TrackerProtocol):
        return Tracker(
            peer_queue=self._peer_que,
            download_bridge=self._bridge,
            protocol=protocol,
            peer_id=self._peer_id,
            file=self.file
        )

    def create_trackers(self) -> List[AbstractTracker]:
        trackers = []
        urls = self.file.announce_list
        for url in urls:
            protocol = self._find_protocol(url)
            if protocol:
                trackers.append(self._create_tracker(protocol))
        return trackers
