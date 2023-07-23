from typing import List

from torrent_client.download.file_loading.file_loader import AbstractFileLoader
from torrent_client.download.file_loading.load_request import LoadRequest
from torrent_client.download.part import Part


class FakeFileLoader(AbstractFileLoader):
    def __init__(self, parts):
        self.parts = parts
        self.start_part_size = None
        self.normal_part_size = None
        self.run_load = False

    async def add_load_request(self, load_req: LoadRequest) -> None:
        pass

    async def listen_to_requests_and_download(self) -> None:
        self.run_load = True


    def create_file_parts(self, start_part_size: int, normal_part_size: int) -> List[Part]:
        self.start_part_size = start_part_size
        self.normal_part_size = normal_part_size
        return self.parts
