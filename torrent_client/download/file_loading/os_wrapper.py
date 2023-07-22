import asyncio
import os
from abc import ABC, abstractmethod

from torrent_client.download.file_loading.os_file import OsFile, AbstractOsFile


class AbstractOsWrapper(ABC):
    @abstractmethod
    async def makedir(self, path: str) -> None:
        pass

    @abstractmethod
    def make_file(self, path: str) -> AbstractOsFile:
        pass

    @abstractmethod
    def is_dir_exist(self, path: str) -> bool:
        pass


class OsWrapper(AbstractOsWrapper):
    async def makedir(self, path: str) -> None:
        await asyncio.to_thread(os.makedirs, path)


    def make_file(self, path: str) -> AbstractOsFile:
        return OsFile(path)

    def is_dir_exist(self, path: str) -> bool:
        return os.path.isdir(path)
