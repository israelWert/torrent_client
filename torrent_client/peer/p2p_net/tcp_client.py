import asyncio
from abc import ABC, abstractmethod
from asyncio import StreamReader, StreamWriter

from torrent_client.peer.exceptions import PeerNotRespondingError


class AbstractTcpClient(ABC):
    @abstractmethod
    async def recv(self, size: int) -> bytes:
        pass

    @abstractmethod
    async def send(self, payload: bytes) -> None:
        pass

    @abstractmethod
    async def init(self):
        pass

    @abstractmethod
    def close(self):
        pass


class TcpClient(AbstractTcpClient):
    def __init__(self, ip: str, port: int):
        self._addr = (ip, port)
        self._reader, self.writer = None, None

    async def init(self):
        try:
            self._reader, self.writer = await asyncio.open_connection(*self._addr)
        except Exception as e:
            raise PeerNotRespondingError("try to open connections and unknown error appeared") from e

    def close(self):
        self.writer.close()

    async def recv(self, size: int) -> bytes:
        return await self._reader.read(size)

    async def send(self, payload: bytes) -> None:
        self.writer.write(payload)
        await self.writer.drain()
