from typing import Tuple

from torrent_client.tracker.tracker_bridge import TrackerBridge


class FakeTrackerBridge(TrackerBridge):
    def get_downloaded_uploaded(self) -> Tuple[int, int]:
        return 0, 0

    def is_downloading(self) -> bool:
        return True