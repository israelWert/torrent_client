from abc import abstractmethod
from typing import Protocol

from torrent_client.download.file_loading.load_request import LoadRequest


class LoadListener(Protocol):
    @abstractmethod
    async def add_load_request(self, load_req: LoadRequest) -> None:
        ...
