from abc import ABC, abstractmethod
from typing import List

from torrent_client.peer.downloading.piece_bitfield_info import PieceBitfieldInfo


class PeerBridge(ABC):
    @abstractmethod
    def store_piece(self, piece: bytes, piece_index: int) -> None:
        pass

    @abstractmethod
    def get_needed_pieces_indexes(self) -> List[int]:
        pass

    @abstractmethod
    def occupy_piece(self, index: int) -> PieceBitfieldInfo:
        pass

    @abstractmethod
    def unlock_piece(self, index: int):
        pass
