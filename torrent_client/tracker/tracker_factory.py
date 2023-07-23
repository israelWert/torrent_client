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


class TrackerFactory(AbstractTrackerFactory):
    def __init__(self, bridge: TrackerBridge, file: TorrentFile, peer_id: str, udp_client: AbstractAsyncUdpClient = None):
        self.file = file
        self.bridge = bridge
        self.udp_client = udp_client if udp_client else AsyncUdpClient()
        self.peer_id = peer_id

    def _find_protocol(self, url) -> Optional[TrackerProtocol]:
        protocol = None
        if "http" in url:
            protocol = HttpTracker(url)
        elif "udp" in url:
            try:
                protocol = UDPTracker(url, self.udp_client)
            except TrackerNotSportedError:
                logger.warning(f"tracker {url} using ip6")
                return None
        else:
            logger.warning(f"tracker {url} with unknown protocol")
        return protocol

    def create_trackers(self) -> List[AbstractTracker]:
        trackers = []
        urls = self.file.announce_list
        for url in urls:
            protocol = self._find_protocol(url)
            if not protocol:
                continue
            trackers.append(Tracker(
                download_bridge=self.bridge,
                protocol=protocol,
                peer_id=self.peer_id,
                file=self.file
            ))
        return trackers
