import asyncio
from abc import ABC, abstractmethod
from asyncio import StreamReader, StreamWriter


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


class TcpClient(AbstractTcpClient):
    def __init__(self, ip: str, port: int):
        self._addr = (ip, port)
        self.reader, self.writer = None, None

    async def init(self):
        self.reader, self.writer = await asyncio.open_connection(*self._addr)

    async def recv(self, size: int) -> bytes:
        return await self.reader.read(size)

    async def send(self, payload: bytes) -> None:
        await self.writer.drain()
