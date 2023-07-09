from abc import abstractmethod, ABC
from typing import List, Iterable
from hashlib import sha1

from torrent_client.constants import BLOCK_SIZE
from torrent_client.peer.exceptions import CorruptedPieceError, NoPieceNeededError
from torrent_client.peer.messages.messages_data import RequestMessage
from torrent_client.peer.piece.peer_bridge import PeerBridge


class AbstractPieceRequestState(ABC):
    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def __iter__(self) -> Iterable[RequestMessage]:
        pass

    @abstractmethod
    def is_piece_complete(self) -> bool:
        pass

    @abstractmethod
    def add_block(self, block: bytes, index: int):
        pass


class PieceRequestState(AbstractPieceRequestState):
    def __init__(self,
                 downloader: PeerBridge,
                 bit_filed: List[bool],
                 ):
        self._downloader = downloader
        self._bit_filed = bit_filed
        self._buffer = b""

    def __enter__(self):
        for piece_index in self._downloader.get_available_pieces_indexes():
            if not self._bit_filed[piece_index]:
                continue
            self._download_data = self._downloader.lock_piece(piece_index)
            break
        else:
            raise NoPieceNeededError()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, Exception):
            self._downloader.unlock_piece(self._download_data.index)
        else:
            self._check_piece_hash()
            self._downloader.store_piece(self._buffer, self._download_data.index)
            self._downloader.unlock_piece(self._download_data.index)

    def _is_hash_valid(self):
        buffer_hash = sha1(self._buffer).digest()
        return buffer_hash == self._download_data.piece_hash

    def _check_piece_hash(self):
        if not self._is_hash_valid():
            self._downloader.unlock_piece(self._download_data.index)
            raise CorruptedPieceError()

    def is_piece_complete(self):
        return self._buffer == self._download_data.piece_length

    def add_block(self, block: bytes, index: int):
        if self._download_data.index != index:
            raise
        self._buffer += block

    def _iter(self) -> Iterable[RequestMessage]:
        for offset in range(0, self._download_data.piece_length, BLOCK_SIZE):
            yield RequestMessage(
                self._download_data.index,
                offset,
                BLOCK_SIZE
            )

    def __iter__(self) -> Iterable[RequestMessage]:
        return self._iter()
