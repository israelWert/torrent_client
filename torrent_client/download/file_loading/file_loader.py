import asyncio
import os
from abc import abstractmethod, ABC
from asyncio import Queue
from typing import List, AsyncIterable

from torrent_client.constants import output_files_path
from torrent_client.download.file_loading.load_listener import LoadListener
from torrent_client.download.file_loading.load_request import LoadRequest
from torrent_client.download.file_loading.os_wrapper import AbstractOsWrapper, OsWrapper
from torrent_client.download.part import Part
from torrent_client.torrent_file.file_to_download import FileToDownload



def join_path_list_with_output_dir(path: List[str]) -> str:
    path = "\\".join(path)
    abs_path = os.path.join(output_files_path, path)
    return abs_path


class AbstractFileLoader(ABC, LoadListener):
    @abstractmethod
    async def add_load_request(self, load_req: LoadRequest) -> None:
        pass

    @abstractmethod
    async def listen_to_requests_and_download(self) -> None:
        pass

    @abstractmethod
    def create_file_parts(self, start_part_size: int, normal_part_size: int) -> List[Part]:
        pass


class FileLoader(AbstractFileLoader):
    def __init__(
            self,
            file: FileToDownload,
            os_wrapper: AbstractOsWrapper):
        self._loading_requests_queue: Queue[LoadRequest] = Queue()
        self._os_wrapper = os_wrapper if os_wrapper else OsWrapper()
        self._parent_path = join_path_list_with_output_dir(file.path[:-1])
        self._path = join_path_list_with_output_dir(file.path)
        self._length = file.length

    async def listen_to_requests_and_download(self):
        await self._handle_directory()
        async with self._os_wrapper.make_file(self._path) as file:
            async for req in self._loading_requests_iter():
                await file.seek(req.beginning_in_file)
                await file.write(req.data)


    async def _handle_directory(self):
        if not self._os_wrapper.is_dir_exist(self._parent_path):
            await self._os_wrapper.makedir(self._parent_path)

    async def _loading_requests_iter(self) -> AsyncIterable[LoadRequest]:
        size_downloaded = 0
        while size_downloaded < self._length:
            req = await self._loading_requests_queue.get()
            size_downloaded += req.size
            yield req


    async def add_load_request(self, load_req: LoadRequest):
        await self._loading_requests_queue.put(load_req)


    def create_file_parts(self, start_part_size: int, normal_part_size: int) -> List[Part]:
        if start_part_size > self._length:
            return [Part(self, self._length, 0)]
        parts = [Part(self, start_part_size, 0)]
        for beginning in range(start_part_size, self._length, normal_part_size):
            size = normal_part_size
            if self._length - beginning < normal_part_size:
                size = self._length - beginning
            parts.append(Part(self, size, beginning))
        return parts
