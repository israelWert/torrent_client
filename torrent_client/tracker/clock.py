import asyncio
import time
from abc import ABC, abstractmethod
from collections import Callable


class AbstractClock(ABC):
    @abstractmethod
    def get_time(self) -> float:
        pass

    @abstractmethod
    async def sleep(self, sec, raise_condition: Callable[[], bool]):
        pass


class Clock(AbstractClock):
    def get_time(self) -> float:
        return time.time()

    async def sleep(self, sec, raise_condition: Callable[[], bool]):
        start_time = time.time()
        while time.time()-start_time != sec:
            if raise_condition():
                break
            await asyncio.sleep(0.1)
