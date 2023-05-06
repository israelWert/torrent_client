from abc import ABC, abstractmethod
from typing import Tuple


class TrackerBridge(ABC):
    @abstractmethod
    def get_downloaded_uploaded(self) -> Tuple[int, int]:
        pass

