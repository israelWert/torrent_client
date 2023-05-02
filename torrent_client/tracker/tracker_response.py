from dataclasses import dataclass
from typing import List, Dict


@dataclass
class TrackerResponse:
    interval: int
    peers: List[Dict[str, str]]
