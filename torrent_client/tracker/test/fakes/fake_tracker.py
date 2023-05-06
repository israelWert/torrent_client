from typing import Optional, List

from torrent_client.tracker.tracker import AbstractTracker


class FakeTracker(AbstractTracker):
    def __init__(self):
        self.has_started = False
        self.was_stop_called = False
        self.has_stop_return = False
        self.peers_to_return = []
        self.error = None

    def start(self):
        self.has_started = True

    def stop(self):
        self.was_stop_called = True

    def has_stopped(self) -> bool:
        return self.has_stop_return

    def get_peers(self) -> Optional[List[dict]]:
        if isinstance(self.error, Exception):
            raise self.error
        return self.peers_to_return
