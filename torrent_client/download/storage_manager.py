from abc import ABC, abstractmethod
from typing import Tuple, List, Optional

from torrent_client.download.file_loading.torrent_loader import TorrentLoader, AbstractTorrentLoader
from torrent_client.download.piece import Piece, AbstractPiece
from torrent_client.peer.downloading.peer_bridge import PeerBridge
from torrent_client.peer.downloading.piece_bitfield_info import PieceBitfieldInfo
from torrent_client.torrent_file.torrent_file import TorrentFile
from torrent_client.tracker.tracker_bridge import TrackerBridge


class AbstractStorageManager(PeerBridge, TrackerBridge, ABC):
    @abstractmethod
    async def download(self) -> None:
        pass


class StorageManager(AbstractStorageManager):
    def __init__(self,
                 torrent_file: TorrentFile,
                 loader: Optional[AbstractTorrentLoader] = None,
                 pieces: Optional[List[AbstractPiece]] = None
                 ):
        self._loader = loader if loader else TorrentLoader(torrent_file.files)
        parts_with_hash = zip(
            self._loader.get_files_parts_in_pieces(torrent_file.piece_length), torrent_file.pieces
        )
        self._pieces = pieces
        if self._pieces:
            self._pieces = [
                Piece(parts, ind, hash_) for ind, (parts, hash_) in enumerate(parts_with_hash)
            ]


    async def download(self) -> None:
        await self._loader.listen_to_requests_and_download()

    def store_piece(self, piece: bytes, piece_index: int) -> None:
        self._pieces[piece_index].download(piece)

    def get_needed_pieces_indexes(self) -> List[int]:
        return [
            ind for ind, piece in enumerate(self._pieces) if piece.is_available_to_download()
        ]

    def occupy_piece(self, index: int) -> PieceBitfieldInfo:
        return self._pieces[index].occupy()

    def unlock_piece(self, index: int):
        self._pieces[index].release()

    def get_downloaded_uploaded(self) -> Tuple[int, int]:
        downloaded = sum(
            piece.get_size() for piece in self._pieces if piece.is_downloaded()
        )
        return downloaded, 0
