import asyncio
import logging

from torrent_client.tracker.clock import AbstractClock
logger = logging.getLogger(__name__)


class FakeClock(AbstractClock):
    def __init__(self):
        self.current_time = 0

    def get_time(self) -> float:
        return self.current_time

    async def sleep(self, sec):
        await asyncio.sleep(0)
        self.current_time += sec
