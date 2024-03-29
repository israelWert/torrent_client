from abc import ABC, abstractmethod
from typing import List

from torrent_client.peer.downloading.peer_bridge import PeerBridge
from torrent_client.peer.downloading.piece_request import PieceDownloader, AbstractPieceDownloader


class AbstractDownloadingManager(ABC):
    @abstractmethod
    def create_piece_downloader(self) -> AbstractPieceDownloader:
        pass

    @abstractmethod
    def set_bitfiled(self, bitfiled: List[bool]):
        pass

    @abstractmethod
    def notify_new_piece(self, index: int):
        pass

    @abstractmethod
    def has_available_piece(self) -> bool:
        pass

    @abstractmethod
    def is_end_downloading(self) -> bool:
        pass


class DownloadingManager(AbstractDownloadingManager):
    def __init__(
            self,
            bitfiled_size: int,
            downloader: PeerBridge
    ):
        self._downloader = downloader
        self._bitfiled_size = bitfiled_size
        self._bitfiled = [False for _ in range(bitfiled_size)]

    def has_available_piece(self) -> bool:
        for piece_index in self._downloader.get_needed_pieces_indexes():
            if self._bitfiled[piece_index]:
                return True
        return False

    def create_piece_downloader(self) -> AbstractPieceDownloader:
        return PieceDownloader(self._downloader, self._bitfiled)

    def set_bitfiled(self, bitfiled: List[bool]):
        self._bitfiled = bitfiled[:self._bitfiled_size]

    def notify_new_piece(self, index: int):
        self._bitfiled[index] = True

    def is_end_downloading(self) -> bool:
        return not self._downloader.get_needed_pieces_indexes()
