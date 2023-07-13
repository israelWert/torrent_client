from typing import List

from torrent_client.peer.downloading.downloading_manager import AbstractDownloadingManager
from torrent_client.peer.downloading.piece_request import AbstractPieceDownloader


class FakeDownloadingManager(AbstractDownloadingManager):
    def __init__(self):
        self.notify_new_piece_data = []
        self.bit_field_response = None
        self.is_have_available_piece_res = True
        self.piece_downloader = None

    def create_piece_downloader(self) -> AbstractPieceDownloader:
        return self.piece_downloader

    def set_bitfiled(self, bitfiled: List[bool]):
        self.bit_field_response = bitfiled

    def notify_new_piece(self, index: int):
        self.notify_new_piece_data.append(index)

    def has_available_piece(self) -> bool:
        return self.is_have_available_piece_res

    def is_end_downloading(self) -> bool:
        return False
