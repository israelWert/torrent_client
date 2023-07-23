import asyncio
from abc import ABC, abstractmethod


class AbstractOsFile(ABC):
    @abstractmethod
    async def __aenter__(self) -> "AbstractOsFile":
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    async def write(self, data: bytes) -> None:
        pass

    @abstractmethod
    async def read(self, size) -> bytes:
        pass

    @abstractmethod
    async def seek(self, pos: int) -> None:
        pass


class OsFile(AbstractOsFile):
    def __init__(self, path):
        self._path = path

    async def __aenter__(self) -> AbstractOsFile:
        self._file = await asyncio.to_thread(open, "rb+", self._path)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await asyncio.to_thread(self._file.close)

    async def read(self, size) -> bytes:
        return await asyncio.to_thread(self._file.read, size)

    async def write(self, data: bytes) -> None:
        await asyncio.to_thread(self._file.write, data)

    async def seek(self, pos: int, whence=0) -> None:
        await asyncio.to_thread(self._file.seek, pos, whence)
