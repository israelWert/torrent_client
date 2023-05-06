import logging

from torrent_client.torrent_file.decoder import AbstractDecoder, Decoder
from torrent_client import log_config
from torrent_client.tracker.test.fakes.fake_tracker_bridge import FakeTrackerBridge
from torrent_client.tracker.tracker_manager import AbstractTrackerManager, TrackerManager
from torrent_client.utils import generate_peer_id

logger = logging.getLogger(__name__)


class Client:
    def __init__(self, file_name=None,
                 decoder: AbstractDecoder = None,
                 tracker_manager: AbstractTrackerManager = None):
        self._peer_id = generate_peer_id()
        self.file_name = file_name
        self.decoder = decoder if decoder else Decoder(file_name)
        self.tracker_manager = tracker_manager if tracker_manager else TrackerManager()

    def download(self,):
        logger.info("************* start download *************")
        file = self.decoder.decode()
        logger.info(f"the file {self.file_name} was decoded successfully")
        logger.debug(f"decoded file: {file}")
        self.tracker_manager.start_trackers(self._peer_id, FakeTrackerBridge(), file)
        logger.info("************* end client *************")
        return file
