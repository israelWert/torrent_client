import asyncio
import logging
from abc import ABC, abstractmethod
import socket

from torrent_client.tracker.clock import AbstractClock, Clock
from torrent_client.tracker.net.udp_net.udp_tracker_messages import UdpTrackerResponse, AbstractUDPMessageManager, \
    UDPMessageManager

logger = logging.getLogger(__name__)


class AbstractAsyncUdpClient(ABC):
    @abstractmethod
    def send_message(self, data: bytes, address: tuple[str, int]) -> None:
        pass

    @abstractmethod
    async def receive_message(self, transaction_id: int, timeout: float) -> UdpTrackerResponse:
        pass

    @abstractmethod
    def close(self):
        pass


class AsyncUdpClient(AbstractAsyncUdpClient):
    def __init__(self, clock: AbstractClock = None, message_manager: AbstractUDPMessageManager = None):
        self.message_manager = message_manager if message_manager else UDPMessageManager()
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self._responses = dict()
        self._listed_task = asyncio.create_task(self._listen())
        self.loop = asyncio.get_running_loop()
        self.clock = clock if clock else Clock()
        self.socket.bind(("0.0.0.0", 81))

    def send_message(self, data: bytes, address: tuple[str, int]) -> None:
        self.socket.sendto(data, address)

    async def receive_message(self, transaction_id: int, timeout: float) -> UdpTrackerResponse:
        end_time = self.clock.get_time() + timeout
        while self.clock.get_time() < end_time:
            if self._responses.get(transaction_id):
                return self._responses.pop(transaction_id)
            await self.clock.sleep(0)

    def close(self):
        self._listed_task.cancel()

    async def _recv_async(self) -> bytes:
        while True:
            self.socket.settimeout(0.001)
            try:
                return self.socket.recv(1500)
            except socket.timeout:
                pass
            await asyncio.sleep(0.1)

    async def _listen(self):
        while True:
            response = await self._recv_async()
            try:
                response = self.message_manager.encode_response_header(response)
                self._responses[response.transaction_id] = response
            except ValueError:
                logger.debug("message didn't have enough data")
