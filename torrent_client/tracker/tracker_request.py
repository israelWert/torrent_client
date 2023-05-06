from dataclasses import dataclass
from typing import Optional

from torrent_client.tracker.event import Event


@dataclass
class TrackerRequest:
    info_hash: bytes
    peer_id: str
    port: int
    uploaded: int
    downloaded: int
    left: int
    event: Optional[Event]
