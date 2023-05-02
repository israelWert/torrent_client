import asyncio
import time
from abc import ABC, abstractmethod


class AbstractClock(ABC):
    @abstractmethod
    def get_time(self) -> float:
        pass

    @abstractmethod
    async def sleep(self, sec):
        pass


class Clock(AbstractClock):
    def get_time(self) -> float:
        return time.time()

    async def sleep(self, sec):
        await asyncio.sleep(sec)
