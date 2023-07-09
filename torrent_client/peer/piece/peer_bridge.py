from abc import ABC, abstractmethod
from typing import List

from torrent_client.peer.piece.piece_download_info import PieceDownloadInfo


class PeerBridge(ABC):
    @abstractmethod
    def store_piece(self, piece: bytes, piece_index: int) -> None:
        pass

    @abstractmethod
    def get_available_pieces_indexes(self) -> List[int]:
        pass

    @abstractmethod
    def lock_piece(self, index: int) -> PieceDownloadInfo:
        pass

    @abstractmethod
    def unlock_piece(self, index: int):
        pass

