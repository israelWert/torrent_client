import asyncio
from typing import List

from torrent_client.peer.downloading.peer_bridge import PeerBridge
from torrent_client.peer.downloading.piece_download_info import PieceDownloadInfo


class FakePeerBridge(PeerBridge):
    def __init__(self):
        self.piece_info = None
        self.available_piece_to_download = []
        self.locked_index = None
        self.unlocked_index = None
        self.blocks = []

    def store_piece(self, piece: bytes, piece_index: int) -> None:
        self.blocks.append((piece, piece_index))

    def get_available_pieces_indexes(self) -> List[int]:
        return self.available_piece_to_download

    def lock_piece(self, index: int) -> PieceDownloadInfo:
        self.locked_index = index
        return self.piece_info

    def unlock_piece(self, index: int):
        self.unlocked_index = index
