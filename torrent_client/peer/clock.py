import asyncio
import time
from abc import ABC, abstractmethod

from torrent_client.peer.exceptions import PeerTimeOutError


class AbstractClock(ABC):
    @abstractmethod
    async def sleep(self, sec: float) -> None:
        pass

    @abstractmethod
    def set_timeout(self, timeout: float) -> None:
        pass

    @abstractmethod
    def reset(self):
        pass


class Clock(AbstractClock):
    def __init__(self):
        self._start_counting_time = time.time()
        self._timeout = 0

    def _check_pass_timeout(self):
        current_time = time.time()
        time_passed = current_time - self._start_counting_time
        if time_passed >= self._timeout:
            raise PeerTimeOutError()

    async def sleep(self, sec: float) -> None:
        self._check_pass_timeout()
        await asyncio.sleep(sec)
        self._check_pass_timeout()

    def set_timeout(self, timeout: float) -> None:
        self._timeout = timeout

    def reset(self):
        self._start_counting_time = time.time()
